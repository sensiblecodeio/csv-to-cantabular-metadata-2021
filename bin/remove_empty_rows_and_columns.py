"""
Create a copy of CSV files in a directory with empty columns and rows removed.

This is a program for use in development. It transforms source files by
removing any columns with an empty heading and any empty rows before
writing them to an output directory.
"""

import sys
import glob
import os
import logging
import csv
from argparse import ArgumentParser

VERSION = '1.2.1-alpha'


def main():
    """Create a copy of CSV files in a directory with empty columns and rows removed."""
    parser = ArgumentParser(
        description='Create a copy of CSV files in a directory with '
                    'empty columns and rows removed.',
        epilog=f'Version: {VERSION}')

    parser.add_argument('-i', '--input-dir',
                        type=str,
                        required=True,
                        help='Input directory containing CSV files to transform')

    parser.add_argument('-o', '--output-dir',
                        type=str,
                        required=True,
                        help='Output directory to write modified files')

    parser.add_argument('-f', '--force-overwrite',
                        action="store_true",
                        required=False,
                        default=False,
                        help='Overwrite any existing files in directory')

    args = parser.parse_args()

    logging.basicConfig(
        format='t=%(asctime)s lvl=%(levelname)s msg=%(message)s', level='INFO')

    for directory in (args.input_dir, args.output_dir):
        if not (os.path.isdir(directory) and os.path.exists(directory)):
            raise ValueError(
                f'{directory!a} does not exist or is not a directory')

    if not args.force_overwrite and len(os.listdir(args.output_dir)) > 0:
        raise ValueError(f'output directory {args.output_dir!a} must be empty')

    if os.path.normpath(args.input_dir) == os.path.normpath(args.output_dir):
        raise ValueError(
            f'output directory {args.output_dir!a} must be different path to input directory')

    for filename in sorted(glob.glob(os.path.join(args.input_dir, '*.csv'))):
        basename = os.path.basename(filename)
        out_filename = os.path.join(args.output_dir, basename)
        with open(out_filename, 'w', encoding='utf-8-sig') as outfile:
            with open(filename, newline='', encoding='utf-8-sig') as infile:
                reader = csv.reader(infile)
                headings = next(reader)
                remove_columns_from_index = len(headings)
                seen_non_empty_column = False

                for i, col in enumerate(reversed(headings)):
                    if len(col.strip()) == 0:
                        if seen_non_empty_column:
                            logging.error(
                                f'Empty cell amongst column headings: {filename!a}, '
                                f'cell {len(headings)-i}')
                            sys.exit(1)
                        remove_columns_from_index = remove_columns_from_index - 1
                    else:
                        seen_non_empty_column = True

                writer = csv.writer(outfile)
                writer.writerow(headings[:remove_columns_from_index])
                lines_removed = 0

                for data_line_index, line in enumerate(reader):
                    line_num = data_line_index + 2
                    content_length = 0
                    trimmed_line = line[:remove_columns_from_index]
                    for cell in trimmed_line:
                        content_length = content_length + len(cell.strip())

                    # Keep this line.
                    if content_length > 0:
                        writer.writerow(trimmed_line)
                        if len(line) < remove_columns_from_index:
                            logging.warning(
                                f'{basename!a}:{line_num} too few cells on row: expected '
                                f'{remove_columns_from_index} but found {len(line)}')
                    else:
                        lines_removed = lines_removed + 1

                    # Warn if data has been lost from line.
                    for i, cell in enumerate(line[remove_columns_from_index:]):
                        if len(cell.strip()) > 0:
                            cell_number = remove_columns_from_index + i
                            logging.warning(
                                f'{basename!a}:{line_num} extra data '
                                f'in cell {cell_number}: "{cell}"')

        logging.info(
            f'Read file from: {basename!a} and wrote modified file to: {out_filename!a}: '
            f'removed {len(headings)-remove_columns_from_index} columns '
            f'and {lines_removed} rows')


if __name__ == '__main__':
    try:
        main()
    except Exception as exception:
        logging.error(exception)
        raise exception
