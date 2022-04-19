"""
Fixup metadata source CSV files.

This is a program for use in development. It modifies source files so that they can successfully
be loaded on ons_csv_to_ctb_main.py.

"""

import glob
import os
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

    args = parser.parse_args()
    for directory in (args.input_dir, args.output_dir):
        if not os.path.isdir(directory):
            raise ValueError(f'{directory} does not exist or is not a directory')

    for filename in glob.glob(os.path.join(args.input_dir, '*.csv')):
        basename = os.path.basename(filename)
        with open(os.path.join(args.output_dir, basename), 'w') as outfile:
            # Main program expects input files in UTF-8 format.
            with open(filename, newline='', encoding='iso-8859-1') as infile:
                for line in infile.read().splitlines():
                    outfile.write(line)
                    outfile.write('\n')

                # Add variables that are referenced elsewhere.
                if basename == 'Variable.csv':
                    outfile.write('4,test_variable_1,Test Var 1,,Test,,,,,,,,PUB,SV,,'
                                  'Person,,,,,,,,1,,,,,,,\n')
                    outfile.write('5,test_variable_2,Test Var 2,,Test,,,,,,,,PUB,SV,,'
                                  'Person,,,,,,,,1,,,,,,,')

                # Add OA to the UR database.
                if basename == 'Database_Variable.csv':
                    outfile.write('3,UR,OA,1,,,,,,,,\n')

                # Add question that is referenced elsewhere.
                if basename == 'Variable_Source_Question.csv':
                    outfile.write('2,cob,test_question_2,,,,,,')


if __name__ == '__main__':
    main()
