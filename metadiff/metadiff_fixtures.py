"""Fixture code."""

import json
import os
import glob


def generate(metadata_server, fixtures_dir, source_metadata):
    """Generate fixtures."""
    for path in glob.glob(os.path.join(fixtures_dir, '*.json')):
        os.remove(path)

    def json_dump(data, filename):
        with open(os.path.join(fixtures_dir, filename), 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=2)

    print('================================================================================')
    print('= Service metadata')
    print('=   contains global metadata shared across all resources')
    print('================================================================================')
    print('Generating fixture for service metadata')
    json_dump(metadata_server.service_query(), 'service.json')
    print()

    print('================================================================================')
    print('= Table metadata')
    print('================================================================================')
    for table in source_metadata.tables():
        print(f'Generating fixture for table: {table}')
        json_dump(metadata_server.table_query(table), f'table.{table}.json')
    print()

    print('================================================================================')
    print('= Dataset metadata')
    print('================================================================================')
    for dataset in source_metadata.datasets():
        print(f'Generating fixture for dataset: {dataset}')
        json_dump(metadata_server.dataset_query(dataset), f'dataset.{dataset}.json')
    print()

    print('================================================================================')
    print('= Variable metadata in base dataset')
    print('=   the metadata service uses a common codebook, with some variables being')
    print('=   modified for specific datasets- the default versions of the variables are')
    print('=   are saved in the base dataset')
    print('================================================================================')
    base_variables = {}
    for variable in source_metadata.variables():
        print(f'Generating fixture for variable: {variable} dataset: base')
        resp = metadata_server.variable_query('base', variable)
        json_dump(resp, f'variable.{variable}.base.json')
        base_variables[variable] = resp
    print()

    print('================================================================================')
    print('= Variable metadata in other datasets')
    print('=   variables that are modified from the shared version in some way, for')
    print('=   instance they may have the Cantabular_Public_Flag set to N')
    print('================================================================================')
    for dataset in source_metadata.datasets():
        for variable in source_metadata.variables():
            resp = metadata_server.variable_query(dataset, variable)
            if resp != base_variables[variable]:
                print(f'Generating fixture for variable: {variable} dataset: {dataset}')
                json_dump(resp, f'variable.{variable}.{dataset}.json')
    print()


class Fixtures:
    """Class to read fixture files."""

    def __init__(self, fixtures_dir):
        """Initialise Fixtures."""
        self.fixtures_dir = fixtures_dir

    def read_file(self, filename):
        """Read a file from the fixtures directory."""
        with open(os.path.join(self.fixtures_dir, filename), 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def datasets(self):
        """Return datasets found in the fixtures."""
        return tuple(sorted([f.split('.')[1] for f in
                             glob.glob(os.path.join(self.fixtures_dir, 'dataset.*.json'))]))

    def variables(self):
        """Return variables found in the fixtures."""
        return tuple(sorted([f.split('.')[1] for f in
                             glob.glob(os.path.join(self.fixtures_dir, 'variable.*.base.json'))]))

    def dataset_variables(self, dataset):
        """Return variables found in the fixtures."""
        return tuple(sorted([f.split('.')[1] for f in
                             glob.glob(os.path.join(self.fixtures_dir,
                                                    f'variable.*.{dataset}.json'))]))

    def tables(self):
        """Return tables found in the fixtures."""
        return tuple(sorted([f.split('.')[1] for f in
                             glob.glob(os.path.join(self.fixtures_dir, 'table.*.json'))]))
