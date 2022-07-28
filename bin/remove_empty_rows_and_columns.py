"""
Create a copy of CSV files in a directory with empty columns and rows removed.

This is a program for use in development. It transforms source files by
removing any columns with an empty heading and any empty rows before
writing them to an output directory.
"""

import glob
import os
import logging
import csv
from argparse import ArgumentParser

VERSION = '1.2.1-alpha'


def main():
    """Create a copy of CSV files in a directory with empty columns and rows removed."""
    parser = ArgumentParser(
        description='Create a copy of CSV files in a directory with'
        ' empty columns and rows removed.',
        epilog=f'Version: {VERSION}')

    parser.add_argument('-i', '--input-dir',
                        type=str,
                        required=True,
                        help='Input directory containing CSV files')

    parser.add_argument('-o', '--output-dir',
                        type=str,
                        required=True,
                        help='Output directory to write modified files')

    args = parser.parse_args()

    logging.basicConfig(
        format='t=%(asctime)s lvl=%(levelname)s msg=%(message)s', level='INFO')

    for directory in (args.input_dir, args.output_dir):
        if not os.path.isdir(directory):
            raise ValueError(
                f'{directory} does not exist or is not a directory')

    for filename in glob.glob(os.path.join(args.input_dir, '*.csv')):
        basename = os.path.basename(filename)
        out_filename = os.path.join(args.output_dir, basename)
        with open(out_filename, 'w', encoding='utf-8-sig') as outfile:
            with open(filename, newline='', encoding='utf-8-sig') as infile:
                reader = csv.reader(infile)
                headings = next(reader)
                removeColumnsAfterIndex = len(headings)
                seenNonEmptyColumn = False

                for i, col in enumerate(reversed(headings)):
                    if len(col.strip()) == 0:
                        if seenNonEmptyColumn:
                            logging.error(
                                f'Empty cell amongst column headings: {filename},'
                                f' cell {len(headings)-i}')
                            exit(1)
                        removeColumnsAfterIndex = removeColumnsAfterIndex - 1
                    else:
                        seenNonEmptyColumn = True

                writer = csv.writer(outfile)
                writer.writerow(headings[:removeColumnsAfterIndex])

                for lineNum, line in enumerate(reader):
                    contentLength = 0
                    trimmedLine = line[:removeColumnsAfterIndex]
                    for cell in trimmedLine:
                        contentLength = contentLength + len(cell.strip())

                    # Keep this line.
                    if contentLength > 0:
                        writer.writerow(trimmedLine)
                        if len(line) < removeColumnsAfterIndex:
                            logging.warning(
                                f'{basename}:{lineNum+2} too few cells on row: expected'
                                f' {removeColumnsAfterIndex} but found {len(line)}')
                    else:
                        logging.info(
                            f'{basename}:{lineNum+2} removed empty line')

                    # Warn if data has been lost from line.
                    for i, cell in enumerate(line[removeColumnsAfterIndex:]):
                        if len(cell.strip()) > 0:
                            c = removeColumnsAfterIndex + i
                            logging.warning(
                                f'{basename}:{lineNum+2} extra data in cell {c}: "{cell}"')

        logging.info(
            f'Read file from: {basename} and wrote modified file to: {out_filename}')


if __name__ == '__main__':
    try:
        main()
    except Exception as exception:
        logging.error(exception)
        raise exception
