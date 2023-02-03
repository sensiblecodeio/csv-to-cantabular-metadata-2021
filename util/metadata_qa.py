"""
Check that datasets on two different instances on cantabular-metadata are the same.

Script leverages the unittest infrastructure and validates that the datasets and variables
on two separate instances of cantabular-metadata are the same. The dataset and variable names
are identified by parsing CSV metadata source files.

Environment variables can be used to set the CSV files directory and the URLs of the metadata
servers.

The tests are split into a number of suites and there are individual tests for English and
Welsh versions.

Some examples of running tests are shown below:

    Run all tests:
    python3 compare_servers.py
    OR
    python3 compare_servers.py

    Run only Welsh tests:
    python3 compare_servers.py DatasetTests CatLabelTests VariableTests -k _cy_


    Run only English tests in CatLabelTests suite:
    python3 compare_servers.py CatLabelTests -k _en_
"""

import csv
import json
import os
import glob
from argparse import ArgumentParser
from urllib.parse import urljoin
import sys
import requests

DATASET_QUERY = """
query($dataset: String!) {
 en: dataset(name: $dataset, lang: "en") {
   all
   description
   label
   name
 }
 cy: dataset(name: $dataset, lang: "cy") {
   all
   description
   label
   name
 }
}
"""

VARIABLE_QUERY = """
query($dataset: String!, $variables: [String!]!) {
 en: dataset(name: $dataset, lang: "en") {
   vars(names: $variables) {
     name
     label
     description
     all
     catLabels
   }
 }
 cy: dataset(name: $dataset, lang: "cy") {
   vars(names: $variables) {
     name
     label
     description
     all
     catLabels
   }
 }
}
"""

TABLE_QUERY = """
query($table: String!) {
  en: service (lang: "en") {
    tables(names: [$table]) {
      name
      description
      label
      datasetName
      vars
      all
    }
  }
  cy: service (lang: "cy") {
    tables(names: [$table]) {
      name
      description
      label
      datasetName
      vars
      all
    }
  }
}
"""

SERVICE_QUERY = """
{
  en: service (lang: "en") {
    all
  }
  cy: service (lang: "cy") {
    all
  }
}
"""


class SourceMetadata:
    """Class to provide information on metadata from files in CSV format."""

    def __init__(self, metadata_dir):
        """Initialise SourceMetadata."""
        if not os.path.isdir(metadata_dir):
            print(f'ERROR: Metadata directory does not exist: {metadata_dir}')
            sys.exit(-1)

        self.metadata_dir = metadata_dir

    def _get_csv_column_values(self, filename, column, conditional_func=None):
        """
        Get the set of values present in a named column in a CSV file.

        The optional conditional_func parameter is a function that can be used to decide
        whether to include a value from a particular row.
        """
        values = set()
        with open(os.path.join(self.metadata_dir, filename), encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row[column]:
                    if conditional_func and not conditional_func(row):
                        continue
                    values.add(row[column].strip())

        return values

    def variables(self):
        """
        Identify all the Cantabular variables from a set of CSV metadata files.

        Cantabular variable names are the set of Codebook_Mnemonic values from Category_Mapping.csv
        along with the Variable_Mnemonic values from Variable.csv for geographic variables.
        """
        def is_geographic(row):
            return row['Variable_Type_Code'] == 'GEOG'

        non_geog_variables = self._get_csv_column_values(
            'Category_Mapping.csv', 'Codebook_Mnemonic')
        geog_variables = sorted(list(self._get_csv_column_values(
            'Variable.csv', 'Variable_Mnemonic', conditional_func=is_geographic)))

        return sorted(list(non_geog_variables.union(geog_variables)))

    def datasets(self):
        """
        Identify all the Cantabular datasets from a set of CSV metadata files.

        Cantabular dataset names are the set of Database_Mnemonic values from Database.csv.
        """
        return sorted(list(self._get_csv_column_values('Database.csv', 'Database_Mnemonic')))

    def tables(self):
        """
        Identify all the Cantabular tables from a set of CSV metadata files.

        Cantabular tables names are the set of Dataset_Mnemonic values from Dataset.csv.
        """
        return sorted(list(self._get_csv_column_values('Dataset.csv', 'Dataset_Mnemonic')))


class FixtureGenerator:
    """Class to generate fixture files."""
    def __init__(self, metadata_server, fixtures_dir, source_metadata):
        """Initialise Fixtures."""
        if not os.path.isdir(fixtures_dir):
            print(f'ERROR: Fixtures directory does not exist: {fixtures_dir}')
            sys.exit(-1)

        for path in glob.glob(os.path.join(fixtures_dir, '*.json')):
            os.remove(path)

        self.metadata_server = metadata_server
        self.fixtures_dir = fixtures_dir
        self.source_metadata = source_metadata

    def json_dump(self, data, filename):
        """Dump data to file in JSON format."""
        with open(os.path.join(self.fixtures_dir, filename), 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=2)

    def generate(self):
        """Perform queries and populate the fixtures."""

        print('================================================================================')
        print('= Service metadata')
        print('=   contains global metadata shared across all resources')
        print('================================================================================')
        print('Generating fixture for service metadata')
        self.json_dump(self.metadata_server.query(SERVICE_QUERY, None), 'service.json')
        print()

        print('================================================================================')
        print('= Table metadata')
        print('================================================================================')
        for table in self.source_metadata.tables():
            print(f'Generating fixture for table: {table}')
            self.json_dump(self.metadata_server.query(TABLE_QUERY, {'table': table}),
                           f'table.{table}.json')
        print()

        print('================================================================================')
        print('= Dataset metadata')
        print('================================================================================')
        for dataset in self.source_metadata.datasets():
            print(f'Generating fixture for dataset: {dataset}')
            self.json_dump(self.metadata_server.query(DATASET_QUERY, {'dataset': dataset}),
                           f'dataset.{dataset}.json')
        print()

        print('================================================================================')
        print('= Variable metadata in base dataset')
        print('=   the metadata service uses a common codebook, with some variables being')
        print('=   modified for specific datasets- the default versions of the variables are')
        print('=   are saved in the base dataset')
        print('================================================================================')
        base_variables = {}
        for variable in self.source_metadata.variables():
            print(f'Generating fixture for variable: {variable} dataset: base')
            resp = self.metadata_server.query(VARIABLE_QUERY,
                                              {'dataset': 'base', 'variables': [variable]})
            self.json_dump(resp, f'variable.{variable}.base.json')
            base_variables[variable] = resp
        print()

        print('================================================================================')
        print('= Variable metadata in other datasets')
        print('=   variables that are modified from the shared version in some way, for')
        print('=   instance they may have the Cantabular_Public_Flag set to N')
        print('================================================================================')
        for dataset in self.source_metadata.datasets():
            for variable in self.source_metadata.variables():
                resp = self.metadata_server.query(VARIABLE_QUERY,
                                                  {'dataset': dataset, 'variables': [variable]})
                if resp != base_variables[variable]:
                    print(f'Generating fixture for variable: {variable} dataset: {dataset}')
                    self.json_dump(resp, f'variable.{variable}.{dataset}.json')
        print()


class Fixtures:
    """Class to read fixture files."""

    def __init__(self, fixtures_dir):
        """Initialise Fixtures."""
        if not os.path.isdir(fixtures_dir):
            print(f'ERROR: Fixtures directory does not exist: {fixtures_dir}')
            sys.exit(-1)

        self.fixtures_dir = fixtures_dir

        self.paths = glob.glob(os.path.join(fixtures_dir, '*.json'))
        self.filenames = [os.path.basename(p) for p in self.paths]
        self._datasets = sorted([f.split('.')[1] for f in
                                 glob.glob(os.path.join(fixtures_dir, 'dataset.*.json'))])
        self._variables = sorted([f.split('.')[1] for f in
                                  glob.glob(os.path.join(fixtures_dir, 'variable.*.base.json'))])
        self._tables = sorted([f.split('.')[1] for f in
                               glob.glob(os.path.join(fixtures_dir, 'table.*.json'))])

    def read_file(self, filename):
        """Read a file from the fixtures directory."""
        with open(os.path.join(self.fixtures_dir, filename), 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def datasets(self):
        """Return datasets found in the fixtures."""
        return tuple(self._datasets)

    def variables(self):
        """Return variables found in the fixtures."""
        return tuple(self._variables)

    def tables(self):
        """Return tables found in the fixtures."""
        return tuple(self._tables)


class MetadataServer:
    """MetadataServer allows communications with a Cantabular metadata server."""
    def __init__(self, metadata_url):
        """Initialise MetadataServer."""
        self.url = urljoin(metadata_url, 'graphql')

    def query(self, graphql_query, graphql_variables):
        """Perform a GraphQL query and return the response."""
        http_resp = requests.post(self.url,
                                  data={'query': graphql_query,
                                        'variables': json.dumps(graphql_variables)})
        http_resp.raise_for_status()
        resp = http_resp.json()
        if 'errors' in resp:
            raise ValueError(f'error for {graphql_variables}')
        return resp


class MetadataComparer:
    """Class contains methods to compare netadata in fixture files with query results."""

    def __init__(self, metadata_server, source_metadata, fixtures):
        """Initialise MetadataComparer."""
        self.metadata_server = metadata_server
        self.source_metadata = source_metadata
        self.fixtures = fixtures

    def compare(self):
        """Perform queries and compare the responses with values in the fixture files."""
        self.compare_service()
        self.compare_datasets()
        self.compare_tables()
        self.compare_variables()

    def compare_service(self):
        """Compare service metadata with data in fixture file."""
        print('================================================================================')
        print('= Comparing service metadata with data on disk')
        print('================================================================================')
        resp = self.metadata_server.query(SERVICE_QUERY, None)
        data = self.fixtures.read_file('service.json')
        if data != resp:
            print('Changes detected in service metadata')
            JSONComparer().compare(data, resp)
            print()
        print()

    def compare_datasets(self):
        """Compare dataset metadata with data in fixture file."""
        print('================================================================================')
        print('= Comparing dataset metadata with data on disk')
        print('================================================================================')
        fixture_datasets = self.fixtures.datasets()
        datasets = self.source_metadata.datasets()
        for dataset in datasets:
            resp = self.metadata_server.query(DATASET_QUERY, {'dataset': dataset})
            if f'dataset.{dataset}.json' in self.fixtures.filenames:
                data = self.fixtures.read_file(f'dataset.{dataset}.json')
                if data != resp:
                    print(f'Changes detected in dataset: {dataset}')
                    JSONComparer().compare(data, resp)
                    print()
            else:
                print(f'New dataset {dataset}')

        deleted_datasets = set(fixture_datasets) - set(datasets)
        if deleted_datasets:
            print('Datasets that are in fixtures but missing from CSV files:', deleted_datasets)
        print()

    def compare_tables(self):
        """Compare table metadata with data in fixture file."""
        print('================================================================================')
        print('= Comparing tables metadata with data on disk')
        print('================================================================================')
        fixture_tables = self.fixtures.tables()
        tables = self.source_metadata.tables()
        for table in tables:
            resp = self.metadata_server.query(TABLE_QUERY, {'table': table})
            if f'table.{table}.json' in self.fixtures.filenames:
                data = self.fixtures.read_file(f'table.{table}.json')
                if data != resp:
                    print(f'Changes detected in table: {table}')
                    JSONComparer().compare(data, resp)
                    print()
            else:
                print(f'New table {table}')

        deleted_tables = set(fixture_tables) - set(tables)
        if deleted_tables:
            print('Tables that are in fixtures but missing from CSV files:', deleted_tables)
        print()

    def compare_variables(self):
        """Compare variable metadata with data in fixture file."""
        fixture_variables = {}
        base_variables = {}

        print('================================================================================')
        print('= Comparing variable metadata with data on disk')
        print('================================================================================')
        variables = self.source_metadata.variables()
        for variable in variables:
            resp = self.metadata_server.query(VARIABLE_QUERY,
                                              {'dataset': 'base', 'variables': [variable]})
            base_variables[variable] = resp
            if f'variable.{variable}.base.json' in self.fixtures.filenames:
                data = self.fixtures.read_file(f'variable.{variable}.base.json')
                fixture_variables[variable] = data
                if data != resp:
                    print(f'Changes detected in variable: {variable}')
                    JSONComparer().compare(data, resp)
                    print()
            else:
                print(f'New variable {variable}')

        for dataset in self.source_metadata.datasets():
            for variable in variables:
                resp = self.metadata_server.query(VARIABLE_QUERY,
                                                  {'dataset': dataset, 'variables': [variable]})
                data = None
                if f'variable.{variable}.{dataset}.json' in self.fixtures.filenames:
                    data = self.fixtures.read_file(f'variable.{variable}.{dataset}.json')
                else:
                    data = fixture_variables.get(variable, None)

                if data and data != resp and resp != base_variables[variable]:
                    print(f'Changes detected in variable: {variable} {dataset}')
                    JSONComparer().compare(data, resp)
                    print()


class JSONComparer:
    """Base class used to compare new and old JSON in a contextual manner."""

    def __init__(self, max_diffs=5):
        """Initialise JSONComparer."""
        self.stack = []
        self.log_spaces = 0
        self.message_count = 0
        self.extra_messages = 0
        self.max_diffs = max_diffs

    def log_messages(self, msgs):
        """Write out the supplied messages."""
        self.message_count += 1
        if self.message_count > self.max_diffs:
            return

        for msg in msgs:
            print(f'{" "*self.log_spaces}{msg}')

    def compare(self, old, new):
        """Start walking through an object, resetting the message count."""
        self.message_count = 0
        self.walk(old, new)
        if self.message_count > self.max_diffs:
            print(f'{" "*self.log_spaces}** PLUS {self.message_count-self.max_diffs} '
                  'additional changes **')

    def walk(self, old, new):
        """
        Compare the values in old and new.
        Report differences and call walk() recursively on complex types.
        """
        if not isinstance(new, type(old)):
            self.log_messages([
                f'Field:{json.dumps(" / ".join(self.stack))}',
                f'  Old value: {old}',
                f'  New value: {new}'])
            return
        if isinstance(old, dict):
            old_fields = set(old.keys())
            new_fields = set(new.keys())
            if new_fields - old_fields:
                self.log_messages([
                    f'Field:{json.dumps(" / ".join(self.stack))}',
                    f'  New fields added: {new_fields-old_fields}'])
            if old_fields - new_fields:
                self.log_messages([
                    f'Field:{json.dumps(" / ".join(self.stack))}',
                    f'  Old fields deleted: {old_fields-new_fields}'])
            for key in sorted(old):
                if key in new:
                    self.stack.append(key)
                    self.walk(old[key], new[key])
                    self.stack.pop()
        elif isinstance(old, list):
            if old != new:
                if len(old) == len(new):
                    for i, old_item in enumerate(old):
                        self.stack.append(f'[{i}]')
                        self.walk(old_item, new[i])
                        self.stack.pop()
                else:
                    self.log_messages([
                        f'Field:{json.dumps(" / ".join(self.stack))}',
                        f'  Old value: {old}',
                        f'  New value: {new}'])
        elif old != new:
            self.log_messages([
                f'Field:{json.dumps(" / ".join(self.stack))}',
                f'  Old value: {repr(old)}',
                f'  New value: {repr(new)}'])


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
                        default='util/qa_fixtures',
                        help='Directory for JSON fixtures i.e. JSON files containing metadata '
                             'for datasets, variables and tables as read from the Cantabular '
                             'metadata service')

    parser.add_argument('-u', '--metadata-url',
                        type=str,
                        required=True,
                        help='URL of metadata service e.g. http://10.10.10.10:8493')

    args = parser.parse_args()

    source_metadata = SourceMetadata(args.metadata_dir)
    metadata_server = MetadataServer(args.metadata_url)

    if args.new_fixtures:
        FixtureGenerator(metadata_server, args.fixtures_dir, source_metadata).generate()
    else:
        fixtures = Fixtures(args.fixtures_dir)
        MetadataComparer(metadata_server, source_metadata, fixtures).compare()


if __name__ == '__main__':
    main()
