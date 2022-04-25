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
    for directory in (args.input_dir, args.output_dir):
        if not os.path.isdir(directory):
            raise ValueError(f'{directory} does not exist or is not a directory')

    logging.basicConfig(format='t=%(asctime)s lvl=%(levelname)s msg=%(message)s', level='INFO')

    for filename in glob.glob(os.path.join(args.input_dir, '*.csv')):
        if args.geography_file and \
                os.path.abspath(filename) == os.path.abspath(args.geography_file):
            continue

        basename = os.path.basename(filename)
        out_filename = os.path.join(args.output_dir, basename)
        with open(out_filename, 'w') as outfile:
            # Main program expects input files in UTF-8 format.
            with open(filename, newline='', encoding='iso-8859-1') as infile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames.copy()
                if basename == 'Category.csv':
                    fieldnames.remove('variable_mnemonic')
                    fieldnames.append('Variable_Mnemonic')

                writer = csv.DictWriter(outfile, fieldnames)
                writer.writeheader()
                for line in reader:
                    if basename == 'Category.csv':
                        line['Variable_Mnemonic'] = line.pop('variable_mnemonic')

                    if basename == 'Variable.csv':
                        line['Security_Mnemonic'] = 'PUB'

                        if not line['Variable_Type_Code']:
                            line['Variable_Type_Code'] = 'DVO'

                    elif basename == 'Classification.csv':
                        if not line['Number_Of_Category_Items']:
                            line['Number_Of_Category_Items'] = '0'

                        if line['Classification_Mnemonic'] == 'hh_away_student_9a':
                            line['Number_Of_Category_Items'] = '8'

                        if line['Classification_Mnemonic'] == 'hh_families_count_7a':
                            line['Number_Of_Category_Items'] = '8'

                        if line['Classification_Mnemonic'] == 'legal_partnership_status_12a':
                            line['Number_Of_Category_Items'] = '12'

                        if line['Classification_Mnemonic'] == 'moving_group_size_10000a':
                            line['Number_Of_Category_Items'] = '9716'

                        if '_pop' in line['Variable_Mnemonic']:
                            continue

                        if line['Classification_Mnemonic'] == 'hh_multi_ethnic_combination_23B':
                            line['Classification_Mnemonic'] = 'hh_multi_ethnic_combination_23b'

                    elif basename == 'Topic_Classification.csv':
                        if line['Classification_Mnemonic'] == 'hh_multi_ethnic_combination_23B':
                            line['Classification_Mnemonic'] = 'hh_multi_ethnic_combination_23b'

                        if line['Classification_Mnemonic'] == 'distance_to_work':
                            line['Classification_Mnemonic'] = 'distance_to_work_12002a'

                        if line['Classification_Mnemonic'] == 'moving_group_number':
                            line['Classification_Mnemonic'] = 'moving_group_number_10000a'

                        if line['Classification_Mnemonic'] == 'moving_group_size':
                            line['Classification_Mnemonic'] = 'moving_group_size_10000a'

                        if line['Classification_Mnemonic'] in [
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
                        if line['Classification_Mnemonic'] == 'armed_forces_dependent_ind_5a':
                            continue

                        if line['Classification_Mnemonic'] == 'moving_group_size':
                            line['Classification_Mnemonic'] = 'moving_group_size_10000a'

                        if '_pop' in line['Classification_Mnemonic']:
                            continue

                    elif basename == 'Dataset.csv':
                        line['Security_Mnemonic'] = 'PUB'

                    elif basename == 'Release_Dataset.csv':
                        line['Census_Release_Number'] = '1'

                    elif basename == 'Dataset_Variable.csv':
                        if line['Classification_Mnemonic'] == 'sex':
                            line['Classification_Mnemonic'] = 'sex_2a'

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
    main()
