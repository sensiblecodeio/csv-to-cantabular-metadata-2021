"""Load metadata from CSV files and export in JSON format."""
import json
import os
import logging
import re
from pathlib import Path
from argparse import ArgumentParser
from datetime import date
from ons_csv_to_ctb_json_load import Loader, PUBLIC_SECURITY_MNEMONIC
from ons_csv_to_ctb_json_bilingual import BilingualDict, Bilingual

VERSION = '1.2.1-alpha'

SYSTEM = 'cantabm'
DEFAULT_CANTABULAR_VERSION = '10.1.0'
CANTABULAR_V10_0_0 = '10.0.0'
CANTABULAR_V9_3_0 = '9.3.0'
CANTABULAR_V9_2_0 = '9.2.0'
FILE_CONTENT_TYPE_DATASET = 'dataset-md'
FILE_CONTENT_TYPE_TABLES = 'tables-md'
FILE_CONTENT_TYPE_SERVICE = 'service-md'
KNOWN_CANTABULAR_VERSIONS = [DEFAULT_CANTABULAR_VERSION, CANTABULAR_V10_0_0, CANTABULAR_V9_3_0,
                             CANTABULAR_V9_2_0]


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
                            epilog=f'Version: {VERSION}')

    parser.add_argument('-i', '--input-dir',
                        type=str,
                        required=True,
                        help='Input directory containing CSV files to convert to JSON')

    parser.add_argument('-o', '--output-dir',
                        type=str,
                        required=True,
                        help='Output directory to write JSON files')

    parser.add_argument('-g', '--geography-file',
                        type=str,
                        required=False,
                        help='Name of CSV file containing category codes and names for geographic '
                             'variables')

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

    args = parser.parse_args()

    logging.basicConfig(format='t=%(asctime)s lvl=%(levelname)s msg=%(message)s',
                        level=args.log_level)

    logging.info(f'{Path(__file__).name} version {VERSION}')
    logging.info(f'CSV source directory: {args.input_dir}')
    if args.geography_file:
        logging.info(f'Geography file: {args.geography_file}')

    for directory in (args.input_dir, args.output_dir):
        if not os.path.isdir(directory):
            raise ValueError(f'{directory} does not exist or is not a directory')

    todays_date = date.today().strftime('%Y%m%d')
    base_filename_template = output_filename_template(
        args.file_prefix, args.cantabular_version, args.metadata_master_version, todays_date,
        args.build_number)

    # loader is used to load the metadata from CSV files and convert it to JSON.
    loader = Loader(args.input_dir, args.geography_file, best_effort=args.best_effort)

    # Build Cantabular variable objects.
    # A Cantabular variable is equivalent to an ONS classification.
    ctb_variables = build_ctb_variables(loader.classifications, loader.categories)

    # Build Cantabular dataset objects.
    # A Cantabular dataset is equivalent to an ONS database.
    ctb_datasets = build_ctb_datasets(loader.databases, ctb_variables)

    # Build Cantabular table objects.
    # A Cantabular table is equivalent to an ONS dataset.
    ctb_tables = build_ctb_tables(loader.datasets)

    # Build Cantabular service metadata.
    service_metadata = build_ctb_service_metadata()

    error_count = loader.error_count()
    if error_count:
        logging.warning(f'{error_count} errors were encountered during processing')

    # There is not a separate tables file for v9.2.0. Use the output_file_types list
    # to determine which file types will be written.
    output_file_types = [FILE_CONTENT_TYPE_DATASET, FILE_CONTENT_TYPE_SERVICE,
                         FILE_CONTENT_TYPE_TABLES]

    if args.cantabular_version == DEFAULT_CANTABULAR_VERSION:
        logging.info(
            f'Output files will be written in Cantabular {args.cantabular_version} format')

    elif args.cantabular_version == CANTABULAR_V9_2_0:
        output_file_types = [FILE_CONTENT_TYPE_DATASET, FILE_CONTENT_TYPE_SERVICE]
        convert_json_to_ctb_v9_2_0(ctb_datasets, ctb_tables, service_metadata)
        logging.info(
            f'Output files will be written in Cantabular {args.cantabular_version} format')

    else:
        logging.info(
            f'{args.cantabular_version} is an unknown Cantabular version: files will be written '
            f'using {DEFAULT_CANTABULAR_VERSION} format')

    if FILE_CONTENT_TYPE_DATASET in output_file_types:
        filename = os.path.join(args.output_dir,
                                base_filename_template.format(FILE_CONTENT_TYPE_DATASET))
        with open(filename, 'w') as jsonfile:
            json.dump(ctb_datasets, jsonfile, indent=4)
        logging.info(f'Written dataset metadata file to: {filename}')

    if FILE_CONTENT_TYPE_TABLES in output_file_types:
        filename = os.path.join(args.output_dir,
                                base_filename_template.format(FILE_CONTENT_TYPE_TABLES))
        with open(filename, 'w') as jsonfile:
            json.dump(ctb_tables, jsonfile, indent=4)
        logging.info(f'Written table metadata file to: {filename}')

    if FILE_CONTENT_TYPE_SERVICE in output_file_types:
        filename = os.path.join(args.output_dir,
                                base_filename_template.format(FILE_CONTENT_TYPE_SERVICE))
        with open(filename, 'w') as jsonfile:
            json.dump(service_metadata, jsonfile, indent=4)
        logging.info(f'Written service metadata file to: {filename}')


def convert_json_to_ctb_v9_2_0(ctb_datasets, ctb_tables, service_metadata):
    """Convert JSON to Cantabular v9.2.0 format."""
    for dataset in ctb_datasets:
        dataset['meta']['description'] = dataset.pop('description')
        for variable in dataset['vars'] if dataset['vars'] else []:
            variable['meta']['description'] = variable.pop('description')

    service_metadata[0]['meta']['tables'] = []
    service_metadata[1]['meta']['tables'] = []
    for table in ctb_tables:
        for idx in [0, 1]:
            localized_table = {
                'name': table['name'],
                'label': table['ref'][idx]['label'],
                'description': table['ref'][idx]['description'],
                'datasetName': table['datasetName'],
                'vars': table['vars'],
                'meta': table['ref'][idx]['meta'],
            }
            service_metadata[idx]['meta']['tables'].append(localized_table)


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


def build_ctb_datasets(databases, ctb_variables):
    """
    Build Cantabular dataset objects.

    A dataset is a built-in concept in cantabular-metadata, and is equivalent to an ONS
    database.
    """
    ctb_datasets = []

    # Add all the variables to a base dataset. Other datasets include this to avoid duplicating
    # metadata.
    ctb_dataset = BilingualDict({
        'name': 'base',
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
    ctb_datasets.extend([ctb_dataset.english(), ctb_dataset.welsh()])

    for database_mnemonic, database in databases.items():
        ctb_dataset = BilingualDict({
            'name': database_mnemonic,
            'incl': [{'name': 'base', 'lang': Bilingual('en', 'cy')}],
            'label': database.private['Database_Title'],
            'description': database.private['Database_Description'],
            'lang': Bilingual('en', 'cy'),
            'meta': database,
            'vars': None,
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


def build_ctb_service_metadata():
    """Build the service metadata."""
    service_metadata = BilingualDict({
        'lang': Bilingual('en', 'cy'),
        'meta': {
            'description': Bilingual(
                'Census 2021 metadata',
                'Census 2021 metadata in Welsh'),
        },
    })
    logging.info(f'Loaded service metadata')

    return [service_metadata.english(), service_metadata.welsh()]


if __name__ == '__main__':
    try:
        main()
    except Exception as exception:
        logging.error(exception)
        raise exception
