"""
Fixup metadata source CSV files.

This is a program for use in development. It modifies source files so that they can successfully
be loaded on ons_csv_to_ctb_main.py.
"""

import glob
import os
import logging
import csv
from argparse import ArgumentParser

VERSION = '1.2.delta'


def main():
    """Fixup metadata source CSV files."""
    parser = ArgumentParser(description='Program for fixing up metadata source CSV files.',
                            epilog=f'Version: {VERSION}')

    parser.add_argument('-i', '--input-dir',
                        type=str,
                        required=True,
                        help='Input directory containing CSV files')

    parser.add_argument('-o', '--output-dir',
                        type=str,
                        required=True,
                        help='Output directory to write fixed-up files')

    args = parser.parse_args()

    logging.basicConfig(format='t=%(asctime)s lvl=%(levelname)s msg=%(message)s', level='INFO')

    for directory in (args.input_dir, args.output_dir):
        if not os.path.isdir(directory):
            raise ValueError(f'{directory} does not exist or is not a directory')

    for filename in glob.glob(os.path.join(args.input_dir, '*.csv')):
        basename = os.path.basename(filename)
        out_filename = os.path.join(args.output_dir, basename)
        with open(out_filename, 'w', encoding='utf-8-sig') as outfile:
            with open(filename, newline='', encoding='utf-8-sig') as infile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames.copy()
                if basename == 'Source.csv' and 'SOURCE_MNEMONIC' in fieldnames:
                    fieldnames.remove('SOURCE_MNEMONIC')
                    fieldnames.append('Source_Mnemonic')
                elif basename == 'Observation_Type.csv' and 'OBSERVATION_TYPE_CODE' in fieldnames:
                    fieldnames.remove('OBSERVATION_TYPE_CODE')
                    fieldnames.append('Observation_Type_Code')
                elif basename == 'Dataset.csv' and 'OBSERVATION_TYPE_CODE' in fieldnames:
                    fieldnames.remove('OBSERVATION_TYPE_CODE')
                    fieldnames.append('Observation_Type_Code')

                writer = csv.DictWriter(outfile, fieldnames)
                writer.writeheader()
                for line in reader:
                    if basename == 'Source.csv' and 'SOURCE_MNEMONIC' in line:
                        line['Source_Mnemonic'] = line.pop('SOURCE_MNEMONIC')
                    elif basename == 'Observation_Type.csv' and 'OBSERVATION_TYPE_CODE' in line:
                        line['Observation_Type_Code'] = line.pop('OBSERVATION_TYPE_CODE')
                    elif basename == 'Dataset.csv':
                        if 'OBSERVATION_TYPE_CODE' in line:
                            line['Observation_Type_Code'] = line.pop('OBSERVATION_TYPE_CODE')
                        if line['Source_Database_Mnemonic'] == 'Resident' or \
                                line['Source_Database_Mnemonic'] == 'Households':
                            line['Source_Database_Mnemonic'] = \
                                line['Source_Database_Mnemonic'].upper()
                    elif basename == 'Database_Variable.csv':
                        line['Source_Classification_Flag'] = \
                            line['Source_Classification_Flag'].upper()
                        line['Cantabular_Public_Flag'] = \
                            line['Cantabular_Public_Flag'].upper()

                    writer.writerow(line)

        logging.info(f'Read file from: {filename} and wrote modified file to: {out_filename}')


if __name__ == '__main__':
    try:
        main()
    except Exception as exception:
        logging.error(exception)
        raise exception
