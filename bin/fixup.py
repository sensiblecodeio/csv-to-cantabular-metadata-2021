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

VERSION = '1.1.alpha'


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

    parser.add_argument('-g', '--geography-file',
                        type=str,
                        required=False,
                        help='Name of geography CSV file')

    args = parser.parse_args()

    logging.basicConfig(format='t=%(asctime)s lvl=%(levelname)s msg=%(message)s', level='INFO')

    for directory in (args.input_dir, args.output_dir):
        if not os.path.isdir(directory):
            raise ValueError(f'{directory} does not exist or is not a directory')

    for filename in glob.glob(os.path.join(args.input_dir, '*.csv')):
        if args.geography_file and \
                os.path.abspath(filename) == os.path.abspath(args.geography_file):
            continue

        basename = os.path.basename(filename)
        out_filename = os.path.join(args.output_dir, basename)
        with open(out_filename, 'w', encoding='utf-8-sig') as outfile:
            # Main program expects input files in UTF-8 format.
            # with open(filename, newline='', encoding='iso-8859-1') as infile:
            with open(filename, newline='', encoding='utf-8-sig') as infile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames.copy()

                writer = csv.DictWriter(outfile, fieldnames)
                writer.writeheader()
                for line in reader:
                    if basename == 'Classification.csv':
                        if '_pop' in line['Variable_Mnemonic']:
                            continue

                        if line['Classification_Mnemonic'] == 'hh_multi_ethnic_combination_23B':
                            line['Classification_Mnemonic'] = 'hh_multi_ethnic_combination_23b'

                    elif basename == 'Topic_Classification.csv':
                        if line['Classification_Mnemonic'] == 'hh_multi_ethnic_combination_23B':
                            line['Classification_Mnemonic'] = 'hh_multi_ethnic_combination_23b'

                        elif line['Classification_Mnemonic'] in [
                                'dwelling_number', 'economic_activity_status_14a',
                                'economic_activity_status_13a', 'economic_activity_status_12b',
                                'economic_activity_status_11a', 'economic_activity_status_11b',
                                'economic_activity_status_10b', 'economic_activity_status_9a',
                                'economic_activity_status_7a', 'economic_activity_status_6a',
                                'economic_activity_status_6b', 'economic_activity_status_5b',
                                'economic_activity_status_4a', 'economic_activity_status_4b',
                                'ethnic_group', 'travel_destination_wz']:
                            continue

                    elif basename == 'Category.csv':
                        if '_pop' in line['Classification_Mnemonic']:
                            continue

                    elif basename == 'Dataset_Variable.csv':
                        line['Variable_Mnemonic'] = line['Variable_Mnemonic'].lower()
                        if line['Variable_Mnemonic'] == 'region':
                            line['Variable_Mnemonic'] = 'reg'
                        elif line['Variable_Mnemonic'] == 'country':
                            line['Variable_Mnemonic'] = 'ctry'

                        if line['Variable_Mnemonic'] == 'oa':
                            line['Lowest_Geog_Variable_Flag'] = 'Y'
                        else:
                            line['Lowest_Geog_Variable_Flag'] = ''

                        if line['Variable_Mnemonic'] in ['oa', 'lsoa', 'msoa', 'la', 'reg',
                                                         'ctry']:
                            line['Processing_Priority'] = ''

                    elif basename == 'Database_Variable.csv':
                        if line['Variable_Mnemonic'] in ['dwelling_number', 'ethnic_group',
                                                         'travel_destination_wz']:
                            continue

                    writer.writerow(line)

                if basename == 'Topic.csv':
                    writer.writerow({
                        'Id': 13,
                        'Topic_Mnemonic': 'HDS',
                        'Topic_Description': 'HDS',
                        'Topic_Description_Welsh': '',
                        'Topic_Title': 'HDS',
                        'Topic_Title_Welsh': ''})
                if basename == 'Database_Variable.csv':
                    row_id = 145
                    lowest_geog_variable_flag = 'Y'
                    for geo in ['oa', 'lsoa', 'msoa', 'la', 'reg', 'ctry']:
                        writer.writerow({
                            'Id': row_id,
                            'Database_Mnemonic': 'UR',
                            'Variable_Mnemonic': geo,
                            'Lowest_Geog_Variable_Flag': lowest_geog_variable_flag,
                            'Version': '1'})
                        row_id += 1
                        lowest_geog_variable_flag = 'N'

                    lowest_geog_variable_flag = 'Y'
                    for geo in ['oa', 'lsoa', 'msoa', 'la', 'reg', 'ctry']:
                        writer.writerow({
                            'Id': row_id,
                            'Database_Mnemonic': 'HH',
                            'Variable_Mnemonic': geo,
                            'Lowest_Geog_Variable_Flag': lowest_geog_variable_flag,
                            'Version': '1'})
                        row_id += 1
                        lowest_geog_variable_flag = 'N'

        logging.info(f'Read file from: {filename} and wrote modified file to: {out_filename}')

    if args.geography_file:
        basename = os.path.basename(args.geography_file)
        out_filename = os.path.join(args.output_dir, basename)
        with open(out_filename, 'w') as outfile:
            with open(args.geography_file, newline='') as infile:
                for line in infile.read().splitlines():
                    line = line.replace(',West Northamptonshireshire,', ',West Northamptonshire,')
                    outfile.write(line)
                    outfile.write('\n')
        logging.info(f'Read geography file from: {args.geography_file} and wrote modified file to:'
                     f' {out_filename}')


if __name__ == '__main__':
    try:
        main()
    except Exception as exception:
        logging.error(exception)
        raise exception
