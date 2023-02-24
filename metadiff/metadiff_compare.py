"""Code to compare responses from queries with fixtures."""

import json


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
        resp = self.metadata_server.service_query()
        data = self.fixtures.read_file('service.json')
        if data != resp:
            print('Changes detected in service metadata')
            compare_json(data, resp)
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
            resp = self.metadata_server.dataset_query(dataset)
            if dataset in fixture_datasets:
                data = self.fixtures.read_file(f'dataset.{dataset}.json')
                if data != resp:
                    print(f'Changes detected in dataset: {dataset}')
                    compare_json(data, resp)
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
            resp = self.metadata_server.table_query(table)
            if table in fixture_tables:
                data = self.fixtures.read_file(f'table.{table}.json')
                if data != resp:
                    print(f'Changes detected in table: {table}')
                    compare_json(data, resp)
                    print()
            else:
                print(f'New table {table}')

        deleted_tables = set(fixture_tables) - set(tables)
        if deleted_tables:
            print('Tables that are in fixtures but missing from CSV files:', deleted_tables)
        print()

    def compare_variables(self):
        """Compare variable metadata with data in fixture file."""
        base_fixtures = {}
        base_responses = {}

        print('================================================================================')
        print('= Comparing variable metadata with data on disk')
        print('================================================================================')
        fixture_variables = self.fixtures.variables()
        variables = self.source_metadata.variables()
        for variable in variables:
            resp = self.metadata_server.variable_query('base', variable)
            base_responses[variable] = resp
            if variable in fixture_variables:
                data = self.fixtures.read_file(f'variable.{variable}.base.json')
                base_fixtures[variable] = data
                if data != resp:
                    print(f'Changes detected in variable: {variable}')
                    compare_json(data, resp)
                    print()
            else:
                print(f'New variable {variable}')

        for dataset in self.source_metadata.datasets():
            dataset_variable_fixtures = self.fixtures.dataset_variables(dataset)
            for variable in variables:
                resp = self.metadata_server.variable_query(dataset, variable)
                data = None
                if variable in dataset_variable_fixtures:
                    data = self.fixtures.read_file(f'variable.{variable}.{dataset}.json')
                elif resp != base_responses[variable]:
                    data = base_fixtures.get(variable, None)

                if data and data != resp:
                    print(f'Changes detected in variable: {variable} {dataset}')
                    compare_json(data, resp)
                    print()

        deleted_variables = set(fixture_variables) - set(variables)
        if deleted_variables:
            print('Variables that are in fixtures but missing from CSV files:', deleted_variables)
        print()


def compare_json(old_json, new_json):
    """Compare the values in old and new and report any differences."""
    field_stack = []

    def log_difference(msg):
        print(f'Field: {json.dumps(" / ".join(field_stack))}')
        print(msg)

    def abridged(value):
        if isinstance(value, list) and len(value) > 10:
            return f'{str(value[0:10])} plus {len(value)-10} items'
        if isinstance(value, dict) and len(value.keys()) > 10:
            short_d = {k: value[k] for k in list(value.keys())[0:10]}
            return f'{str(short_d)} plus {len(value)-10} items'
        return value

    def walk(old, new):
        if not isinstance(new, type(old)):
            log_difference(f'  Old value: {old}\n  New value: {abridged(new)}')
            return
        if isinstance(old, dict):
            old_fields = set(old.keys())
            new_fields = set(new.keys())
            if new_fields - old_fields:
                msg = f'  New fields added: {new_fields-old_fields}'
                for field in new_fields - old_fields:
                    msg += f'\n    {field}: {new[field]}'
                log_difference(msg)
            if old_fields - new_fields:
                log_difference(f'  Old fields deleted: {old_fields-new_fields}')
            for key in sorted(old):
                if key in new:
                    field_stack.append(key)
                    walk(old[key], new[key])
                    field_stack.pop()
        elif isinstance(old, list):
            if old != new:
                if len(old) == len(new):
                    for i, old_item in enumerate(old):
                        field_stack.append(f'[{i}]')
                        walk(old_item, new[i])
                        field_stack.pop()
                else:
                    log_difference(f'  Old value: {old}\n  New value: {new}')
        elif old != new:
            log_difference(f'  Old value: {repr(old)}\n  New value: {repr(new)}')

    walk(old_json, new_json)
