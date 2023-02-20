"""Load metadata from CSV files and export in JSON format."""
import json
import os
import logging
import re
import glob
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime
from ons_csv_to_ctb_json_load import Loader, PUBLIC_SECURITY_MNEMONIC
from ons_csv_to_ctb_json_bilingual import BilingualDict, Bilingual

SCHEMA_VERSION = '1.3'

# The first two elements in SCRIPT_VERSION refer to the metadata schema. The final element is the
# iteration of the conversion code for that version of the schema.
SCRIPT_VERSION = SCHEMA_VERSION + '.3'

SYSTEM = 'cantabm'
DEFAULT_CANTABULAR_VERSION = '10.2.2'
CANTABULAR_V10_2_1 = '10.2.1'
CANTABULAR_V10_2_0 = '10.2.0'
CANTABULAR_V10_1_1 = '10.1.1'
CANTABULAR_V10_1_0 = '10.1.0'
CANTABULAR_V10_0_0 = '10.0.0'
CANTABULAR_V9_3_0 = '9.3.0'
FILE_CONTENT_TYPE_DATASET = 'dataset-md'
FILE_CONTENT_TYPE_TABLES = 'tables-md'
FILE_CONTENT_TYPE_SERVICE = 'service-md'
KNOWN_CANTABULAR_VERSIONS = [DEFAULT_CANTABULAR_VERSION, CANTABULAR_V10_2_1, CANTABULAR_V10_2_0,
                             CANTABULAR_V10_1_1, CANTABULAR_V10_1_0, CANTABULAR_V10_0_0,
                             CANTABULAR_V9_3_0]


def filename_segment(value):
    """Check that the string is valid for use as part of a filename."""
    for character in value:
        if not character.isalnum() and character not in '-_. ':
            raise ValueError(f"invalid value: '{value}'")
    return value


def positive_int(value):
    """Check that the value is an integer greater or equal to 0."""
    # An exception will be raised if value is not an int
    number = int(value)
    if number < 0:
        raise ValueError(f"invalid value: '{value}'")
    return number


def cantabular_version_string(value):
    """Check that the version is of format x.y.z."""
    value = value.strip()
    if not re.match(r'^\d+.\d+.\d+$', value):
        raise ValueError(f"invalid value: '{value}'")
    return value


def main():
    """
    Load metadata in CSV format and export in JSON format.

    The exported JSON files can be loaded by cantabular-metadata.
    """
    parser = ArgumentParser(description='Program for converting metadata files in CSV format to '
                                        'JSON format that can be loaded into cantabular-metadata.',
                            epilog=f'Version: {SCRIPT_VERSION}')

    parser.add_argument('-i', '--input-dir',
                        type=str,
                        required=True,
                        help='Input directory containing CSV files to convert to JSON')

    parser.add_argument('-o', '--output-dir',
                        type=str,
                        required=True,
                        help='Output directory to write JSON files')

    # Keeping the -g parameter maintains backwards compatibility to case where only a single
    # geography file was supported. The list of files could be quite long, so also adding
    # the -d option.
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-g', '--geography-files',
                       type=str,
                       required=False,
                       help='Names of CSV files containing category codes and names for '
                            'geographic variables, supplied as a comma separated list')

    group.add_argument('-d', '--geography-dir',
                       type=str,
                       required=False,
                       help='Folder containing CSV files with category codes and names for '
                            'geographic variables')

    parser.add_argument('-l', '--log_level',
                        type=str,
                        default='INFO',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help='Log level (default: %(default)s)')

    parser.add_argument('-p', '--file_prefix',
                        type=str,
                        choices=['d', 't', 'tu'],
                        help='Prefix to use in output filenames: d=dev, t=test, tu=tuning '
                             '(default: no prefix i.e. operational)')

    parser.add_argument('-m', '--metadata_master_version',
                        type=filename_segment,
                        default='unknown-metadata-version',
                        help='Metadata master version to use in output filenames '
                             '(default: %(default)s)')

    parser.add_argument('-b', '--build_number',
                        type=positive_int,
                        default=1,
                        help='Build number to use in output filenames '
                             '(default: %(default)s)')

    parser.add_argument('-v', '--cantabular-version',
                        type=cantabular_version_string,
                        default=DEFAULT_CANTABULAR_VERSION,
                        help='Cantabular version for output files. The supported versions are '
                             f'[{", ".join(KNOWN_CANTABULAR_VERSIONS)}]. If any other version is '
                             'supplied then it will be used in the filename, but version '
                             f'{DEFAULT_CANTABULAR_VERSION} formatting will be used. '
                             '(default: %(default)s)')

    parser.add_argument('--best-effort',
                        action='store_true',
                        help='Discard invalid data instead of failing on the first error and '
                             'make a best effort attempt to produce valid output files.')

    parser.add_argument('--dataset-filter',
                        type=str,
                        default='',
                        help='Comma separated list of Dataset_Mnemonic prefixes. Only datasets '
                             'that have a Dataset_Mnemonic beginning with one of these values '
                             'will be processed. Each element in the list will be stripped of '
                             'leading and trailing whitespace. All records relating to other '
                             'datasets will be discarded '
                             'e.g. use "--dataset-filter TS" to only include datasets '
                             'with a Dataset_Mnemonic beginning with TS, or '
                             '"--dataset-filter TS,RM" to include datasets with a '
                             'Dataset_Mnemonic beginning with either TS or RM.')

    parser.add_argument('--base-dataset-name',
                        type=str,
                        default='base',
                        help='Name to use for virtual base dataset which contains all variables '
                             'and which all other datasets include. The purpose of this dataset '
                             'is to minimise the size of the dataset JSON file by avoiding '
                             'duplication of variable data- the base dataset does not have to '
                             'exist as an actual Cantabular dataset.')

    args = parser.parse_args()

    logging.basicConfig(format='t=%(asctime)s lvl=%(levelname)s msg=%(message)s',
                        level=args.log_level)

    logging.info(f'{Path(__file__).name} version {SCRIPT_VERSION}')
    logging.info(f'CSV source directory: {args.input_dir}')
    geography_files = []
    if args.geography_files:
        geography_files = [fn.strip() for fn in args.geography_files.split(',')]
        seen = set()
        dupes = [fn for fn in geography_files if fn in seen or seen.add(fn)]
        if dupes:
            raise ValueError(f'Some geography filenames are specified multiple times: {dupes}')
    elif args.geography_dir:
        if not os.path.isdir(args.geography_dir):
            raise ValueError(f'{args.geography_dir} does not exist or is not a directory')
        geography_files = sorted(glob.glob(os.path.join(args.geography_dir, '*.csv')))

    if geography_files:
        logging.info(f'Geography files: {",".join(geography_files)}')
    if args.dataset_filter:
        logging.info(f'Dataset filter: {args.dataset_filter}')

    for directory in (args.input_dir, args.output_dir):
        if not os.path.isdir(directory):
            raise ValueError(f'{directory} does not exist or is not a directory')

    time_now = datetime.now()
    todays_date = time_now.strftime('%Y%m%d')
    build_time = time_now.isoformat()

    base_filename_template = output_filename_template(
        args.file_prefix, args.cantabular_version, args.metadata_master_version, todays_date,
        args.build_number)

    # loader is used to load the metadata from CSV files and convert it to JSON.
    loader = Loader(args.input_dir, geography_files, best_effort=args.best_effort,
                    dataset_filter=args.dataset_filter)

    # Build Cantabular variable objects.
    # A Cantabular variable is equivalent to an ONS classification.
    ctb_variables = build_ctb_variables(loader.classifications, loader.categories)

    # Build Cantabular dataset objects.
    # A Cantabular dataset is equivalent to an ONS database.
    ctb_datasets = build_ctb_datasets(loader.databases, ctb_variables, args.base_dataset_name)

    # Build Cantabular table objects.
    # A Cantabular table is equivalent to an ONS dataset.
    ctb_tables = build_ctb_tables(loader.datasets)

    # Build Cantabular service metadata.
    service_metadata = build_ctb_service_metadata(loader.metadata_version_number, build_time,
                                                  geography_files, args)

    error_count = loader.error_count()
    if error_count:
        logging.warning(f'{error_count} errors were encountered during processing')

    if args.cantabular_version in KNOWN_CANTABULAR_VERSIONS:
        logging.info(
            f'Output files will be written in Cantabular {args.cantabular_version} format, '
            f'which is compatible with all versions of Cantabular from {CANTABULAR_V9_3_0} '
            f'to {DEFAULT_CANTABULAR_VERSION}')
    else:
        logging.info(
            f'{args.cantabular_version} is an unknown Cantabular version: files will be written '
            f'using {DEFAULT_CANTABULAR_VERSION} format')

    logging.info('Build '
                 f'created={build_time} '
                 f'best_effort={args.best_effort} '
                 f'dataset_filter={json.dumps(args.dataset_filter)} '
                 f'geography_file={json.dumps(basename_string(geography_files))} '
                 f'versions_data={loader.metadata_version_number} '
                 f'versions_schema={SCHEMA_VERSION} '
                 f'versions_script={SCRIPT_VERSION}')

    filename = os.path.join(args.output_dir,
                            base_filename_template.format(FILE_CONTENT_TYPE_DATASET))
    with open(filename, 'w') as jsonfile:
        json.dump(ctb_datasets, jsonfile, indent=4)
    logging.info(f'Written dataset metadata file to: {filename}')

    filename = os.path.join(args.output_dir,
                            base_filename_template.format(FILE_CONTENT_TYPE_TABLES))
    with open(filename, 'w') as jsonfile:
        json.dump(ctb_tables, jsonfile, indent=4)
    logging.info(f'Written table metadata file to: {filename}')

    filename = os.path.join(args.output_dir,
                            base_filename_template.format(FILE_CONTENT_TYPE_SERVICE))
    with open(filename, 'w') as jsonfile:
        json.dump(service_metadata, jsonfile, indent=4)
    logging.info(f'Written service metadata file to: {filename}')


def output_filename_template(prefix, cantabular_version, metadata_master_version, todays_date,
                             build_number):
    """Generate template for output filename."""
    system_software_version = 'v' + cantabular_version.replace('.', '-')
    filename = (f'{SYSTEM}_{system_software_version}_{metadata_master_version}_{{}}_'
                f'{todays_date}-{build_number}.json')
    if prefix:
        filename = prefix + '_' + filename

    return filename


def build_ctb_variables(classifications, cat_labels):
    """
    Build Cantabular variable objects.

    A variable is a built-in concept in cantabular-metadata, and is equivalent to an ONS
    classification.
    """
    ctb_variables = []
    for mnemonic, classification in classifications.items():
        # Only export public variables.
        if classification.private['Security_Mnemonic'] != PUBLIC_SECURITY_MNEMONIC:
            logging.info(f'Dropped non public classification: {mnemonic}')
            continue

        ctb_class = {
            'name': classification.private['Codebook_Mnemonic'],
            'label': classification.private['Classification_Label'],
            'description': classification.private['Variable_Description'],
            'meta': classification,
            'catLabels': cat_labels.get(mnemonic, None)
        }
        ctb_variables.append(BilingualDict(ctb_class))
        logging.debug(f'Loaded metadata for Cantabular variable: {mnemonic}')

    logging.info(f'Loaded metadata for {len(ctb_variables)} Cantabular variables')

    return ctb_variables


def non_public_variable(classification_mnemonic):
    """Create a dataset specific variable with Cantabular_Public_Flag set to N."""
    return {
        'name': classification_mnemonic,
        'meta': {'Cantabular_Public_Flag': 'N'},
        'catLabels': None,
    }


def build_ctb_datasets(databases, ctb_variables, base_dataset_name):
    """
    Build Cantabular dataset objects.

    A dataset is a built-in concept in cantabular-metadata, and is equivalent to an ONS
    database.
    """
    ctb_datasets = []

    # Add all the variables to a base dataset. Other datasets include this to avoid duplicating
    # metadata.
    ctb_dataset = BilingualDict({
        'name': base_dataset_name,
        'label': Bilingual(
            'Base dataset with metadata for all variables',
            'Base dataset with metadata for all variables in Welsh',
        ),
        'lang': Bilingual('en', 'cy'),
        'description': Bilingual(
            'This is a base dataset containing metadata for all variables used across all '
            'other datasets. Other datasets include it to avoid duplicating metadata.',
            'This is the Welsh version of the base dataset containing metadata for all '
            'variables.'),
        'meta': {
            'Source': {
                'Source_Mnemonic': 'Census2021',
                'Source_Description': 'The 2021 England and Wales Census',
                'Version': '1',
            },
            'Version': '1',
            'Database_Type': {
                'Database_Type_Code': 'BASE',
                'Database_Type_Description': 'Base dataset containing metadata for all variables '
                                             'used across all other datasets',
            }
        },
        'vars': ctb_variables,
    })

    # Include the English dataset in the Welsh dataset. This ensures that the Welsh output from the
    # metadata server will include English category labels that do not have Welsh values.
    welsh_dataset = ctb_dataset.welsh()
    welsh_dataset['incl'] = [{'name': base_dataset_name, 'lang': 'en'}]

    ctb_datasets.extend([ctb_dataset.english(), welsh_dataset])

    uc_base_dataset_name = base_dataset_name.upper()
    for database_mnemonic, database in databases.items():
        if database_mnemonic.upper() == uc_base_dataset_name:
            raise ValueError('Dataset has same case insensitive name as base dataset: '
                             f'{base_dataset_name}')
        ctb_dataset = BilingualDict({
            'name': database_mnemonic,
            'incl': [{'name': base_dataset_name, 'lang': Bilingual('en', 'cy')}],
            'label': database.private['Database_Title'],
            'description': database.private['Database_Description'],
            'lang': Bilingual('en', 'cy'),
            'meta': database,
            'vars':
                [non_public_variable(np) for np in
                 database.private['Non_Public_Classifications']] if
                database.private['Non_Public_Classifications'] else None,
        })
        ctb_datasets.extend([ctb_dataset.english(), ctb_dataset.welsh()])
        logging.debug(f'Loaded metadata for Cantabular dataset: {database_mnemonic}')

    logging.info(f'Loaded metadata for {len(databases)} Cantabular datasets')

    return ctb_datasets


def build_ctb_tables(datasets):
    """
    Build the metadata for each predefined table.

    A Cantabular table is equivalent to an ONS dataset.
    """
    ctb_tables = []
    for mnemonic, dataset in datasets.items():
        # Only export public tables.
        if datasets[mnemonic].private['Security_Mnemonic'] != PUBLIC_SECURITY_MNEMONIC:
            logging.info(f'Dropped non public ONS Dataset: {mnemonic}')
            continue

        ref = BilingualDict({
            'lang': Bilingual('en', 'cy'),
            'label': dataset.private['Dataset_Title'],
            'description': dataset.private['Dataset_Description'],
            'meta': dataset,
        })

        table = {
            'name': mnemonic,
            'datasetName': dataset.private['Database_Mnemonic'],
            'vars': dataset.private['Codebook_Mnemonics'],
            'ref': [ref.english(), ref.welsh()],
        }

        ctb_tables.append(table)
        logging.debug(f'Loaded metadata for Cantabular table: {mnemonic}')

    logging.info(f'Loaded metadata for {len(ctb_tables)} Cantabular tables')

    return ctb_tables


def build_ctb_service_metadata(metadata_version_number, build_time, geography_files, args):
    """Build the service metadata."""
    service_metadata = BilingualDict({
        'lang': Bilingual('en', 'cy'),
        'meta': {
            'description': Bilingual(
                'Census 2021 metadata',
                'Census 2021 metadata in Welsh'),
            'build': {
                'created': build_time,
                'dataset_filter': args.dataset_filter if args.dataset_filter else None,
                'best_effort': str(args.best_effort),
                # The geography files would be better as a list. However, that would involve an
                # API change and could potentially requires updates to existing software using the
                # metadata service. Sticking with a string as this field is for debug purposes
                # only.
                'geography_file': basename_string(geography_files) if geography_files else None,
                'versions': {
                    'data': metadata_version_number,
                    'schema': SCHEMA_VERSION,
                    'script': SCRIPT_VERSION,
                },
            },
        },
    })
    logging.info(f'Loaded service metadata')

    return [service_metadata.english(), service_metadata.welsh()]


def basename_string(filenames):
    """Return a comma separate list of basenames of a list of files."""
    return ','.join([os.path.basename(fn) for fn in filenames])


if __name__ == '__main__':
    try:
        main()
    except Exception as exception:
        logging.error(exception)
        raise exception
