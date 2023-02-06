"""
Program to check how metadata served up by cantabular-metadata has changed from a previous run.

The program identifies the set of datasets, tables and variables available in the metadata by
parsing the relevant sourcs CSV files. It then runs queries against cantabular-metadata for every
dataset, table and variable in each dataset. It compares the responses with a set of fixtures and
reports on the differences.

The fixtures can be generated using the -n flag.
"""

import os
from argparse import ArgumentParser
import sys
from metadiff_server import MetadataServer
from metadiff_fixtures import Fixtures, generate
from metadiff_source import SourceMetadata
from metadiff_compare import MetadataComparer


def main():
    """Do queries."""
    parser = ArgumentParser(description='Program for checking what metadata has changed.')

    parser.add_argument('-n', '--new-fixtures',
                        action='store_true',
                        help='Create new test fixtures')

    parser.add_argument('-m', '--metadata-dir',
                        type=str,
                        required=True,
                        help='Directory containing metadata files in CSV format')

    parser.add_argument('-f', '--fixtures-dir',
                        type=str,
                        required=False,
                        default='metadiff/fixtures',
                        help='Directory for JSON fixtures i.e. JSON files containing metadata '
                             'for datasets, variables and tables as read from the Cantabular '
                             'metadata service')

    parser.add_argument('-u', '--metadata-url',
                        type=str,
                        required=True,
                        help='URL of metadata service e.g. http://10.10.10.10:8493')

    args = parser.parse_args()

    if not os.path.isdir(args.fixtures_dir):
        print(f'ERROR: Fixtures directory does not exist: {args.fixtures_dir}')
        sys.exit(-1)

    if not os.path.isdir(args.metadata_dir):
        print(f'ERROR: Metadata directory does not exist: {args.metadata_dir}')
        sys.exit(-1)

    source_metadata = SourceMetadata(args.metadata_dir)
    metadata_server = MetadataServer(args.metadata_url)

    if args.new_fixtures:
        generate(metadata_server, args.fixtures_dir, source_metadata)
    else:
        fixtures = Fixtures(args.fixtures_dir)
        MetadataComparer(metadata_server, source_metadata, fixtures).compare()


if __name__ == '__main__':
    main()
