"""
Fixup metadata source CSV files.

This is a program for use in development. It modifies source files so that they can successfully
be loaded on ons_csv_to_ctb_main.py.

"""

import glob
import os
import logging
from argparse import ArgumentParser

VERSION = '1.0.beta'


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
                for line in infile.read().splitlines():
                    if basename == 'Dataset.csv':
                        line = line.replace(',OA,', ',LAD,')

                    outfile.write(line)
                    outfile.write('\n')

                # Add variables that are referenced elsewhere.
                if basename == 'Variable.csv':
                    outfile.write('4,test_variable_1,Test Var 1,,Test,,,,,,,,PUB,SV,,'
                                  'Person,,,,,,,,1,,,,,,,\n')
                    outfile.write('5,test_variable_2,Test Var 2,,Test,,,,,,,,PUB,SV,,'
                                  'Person,,,,,,,,1,,,,,,,\n')
                    outfile.write('6,LAD,Local Authority Districts,,'
                                  'Local Authority Districts,,,,,,,,PUB,GEOG,,,,LAD,,,,England,,1'
                                  ',,,,,,,\n')

                # Add OA to the UR database.
                if basename == 'Database_Variable.csv':
                    outfile.write('3,UR,OA,1,,,,,,,,\n')
                    outfile.write('4,UR,LAD,1,,,,,,,,\n')

                # Add question that is referenced elsewhere.
                if basename == 'Variable_Source_Question.csv':
                    outfile.write('2,cob,test_question_2,,,,,,')
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
