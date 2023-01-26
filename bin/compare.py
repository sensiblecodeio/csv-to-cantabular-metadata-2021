"""Load metadata from CSV files and export in JSON format."""
import json
import logging
from pathlib import Path
from argparse import ArgumentParser

VERSION = '1.3.alpha'


class Comparer:
    """Base class used to compare new and old JSON in a contextual manner."""

    def __init__(self, max_diffs):
        """Initialise Comparer."""
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

    def start_walk(self, old, new):
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
                self.log_messages([f'New fields added: {new_fields-old_fields}'])
            if old_fields - new_fields:
                self.log_messages([f'Old fields deleted: {old_fields-new_fields}'])
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


class DatasetComparer(Comparer):
    """Comparer for dataset files."""

    def __init__(self, max_diffs, old_dataset, new_dataset):
        """Initialise DatasetComparer."""
        old_name = old_dataset.pop('name')
        new_name = new_dataset.pop('name')
        if old_name != new_name:
            raise ValueError(f'Datasets have different names: {old_name} and {new_name}')

        old_lang = old_dataset.pop('lang')
        new_lang = new_dataset.pop('lang')
        if old_lang != new_lang:
            raise ValueError(f'Datasets have different languages: {old_lang} and {new_lang}')

        self.dataset_string = f'{old_name} ({old_lang})'

        self.old_vars = {v['name']: v for v in old_dataset.pop('vars')} \
            if old_dataset['vars'] else {}
        self.new_vars = {v['name']: v for v in new_dataset.pop('vars')} \
            if new_dataset['vars'] else {}

        self.old_dataset = old_dataset
        self.new_dataset = new_dataset

        self.variable = ""
        self._dataset_logged = False
        self._variable_logged = None
        super().__init__(max_diffs)

    def log_dataset(self):
        """Print dataset name if not already printed."""
        if not self._dataset_logged:
            print(f'Dataset: {self.dataset_string}')
            self._dataset_logged = True
            self.log_spaces += 2

    def log_variable(self):
        """Print variable name if not already printed."""
        self.log_dataset()
        if self._variable_logged and self._variable_logged != self.variable:
            self.log_spaces -= 2
            self._variable_logged = None

        if self.variable and self._variable_logged != self.variable:
            print(f'{" "*self.log_spaces}Variable: {self.variable}')
            self._variable_logged = self.variable
            self.log_spaces += 2

    def log_messages(self, msgs):
        """Write out the supplied messages."""
        self.log_variable()
        super().log_messages(msgs)

    def compare(self):
        """Compare the fields in the new and old dataset."""
        self.walk(self.old_dataset, self.new_dataset)

        old_var_names = set(self.old_vars.keys())
        new_var_names = set(self.new_vars.keys())

        self.message_count = 0
        if new_var_names - old_var_names:
            self.log_messages([f'New variables added: {new_var_names - old_var_names}'])
        if old_var_names - new_var_names:
            self.log_messages([f'Deleted variables: {old_var_names - new_var_names}'])

        for var_name in sorted(new_var_names.intersection(old_var_names)):
            self.variable = var_name
            self.start_walk(self.old_vars[var_name], self.new_vars[var_name])
            self.variable = ""


class TableComparer(Comparer):
    """Comparer for table files."""

    def __init__(self, max_diffs, old_table, new_table):
        """Initialise TableComparer."""
        old_name = old_table.pop('name')
        new_name = new_table.pop('name')
        if old_name != new_name:
            raise ValueError(f'Tables have different names: {old_name} and {new_name}')

        self.name = old_name
        self.old_table = old_table
        self.new_table = new_table
        self.table_logged = False
        super().__init__(max_diffs)

    def log_table(self):
        """Print table name if not already printed."""
        if not self.table_logged:
            print(f'Table: {self.name}')
            self.table_logged = True
            self.log_spaces += 2

    def log_messages(self, msgs):
        """Write out the supplied messages."""
        self.log_table()
        super().log_messages(msgs)

    def compare(self):
        """Compare each table."""
        self.start_walk(self.old_table, self.new_table)


def main():
    """
    Load metadata in CSV format and export in JSON format.

    The exported JSON files can be loaded by cantabular-metadata.
    """
    parser = ArgumentParser(description='Program for converting metadata files in CSV format to '
                                        'JSON format that can be loaded into cantabular-metadata.',
                            epilog=f'Version: {VERSION}')

    parser.add_argument('-o', '--old-file',
                        type=str,
                        required=True,
                        help='Old file')

    parser.add_argument('-n', '--new-file',
                        type=str,
                        required=True,
                        help='Old file')

    parser.add_argument('-l', '--log_level',
                        type=str,
                        default='INFO',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help='Log level (default: %(default)s)')

    parser.add_argument('-t', '--file_type',
                        type=str,
                        required=True,
                        choices=['TABLES', 'DATASETS'],
                        help='File type')

    parser.add_argument('-m', '--max_diffs',
                        type=int,
                        default=10,
                        help='Build number to use in output filenames '
                             '(default: %(default)s)')

    args = parser.parse_args()

    logging.basicConfig(format='t=%(asctime)s lvl=%(levelname)s msg=%(message)s',
                        level=args.log_level)

    logging.info(f'{Path(__file__).name} version {VERSION}')

    args.max_diffs = max(args.max_diffs, 1)

    with open(args.old_file, 'r', encoding='utf-8') as old_file:
        old_data = json.load(old_file)

    with open(args.new_file, 'r', encoding='utf-8') as new_file:
        new_data = json.load(new_file)

    if args.file_type == 'DATASETS':
        old_datasets = {(d['name'], d['lang']): d for d in old_data}
        new_datasets = {(d['name'], d['lang']): d for d in new_data}
        print(f'New datasets: {sorted(new_datasets.keys()-old_datasets.keys())}')
        print(f'Deleted datasets: {sorted(old_datasets.keys()-new_datasets.keys())}')

        for (name, lang) in sorted(
                set(old_datasets.keys()).intersection(set(new_datasets.keys()))):
            DatasetComparer(
                args.max_diffs,
                old_datasets[(name, lang)],
                new_datasets[(name, lang)]).compare()
    else:
        old_tables = {t['name']: t for t in old_data}
        new_tables = {t['name']: t for t in new_data}
        print(f'New tables: {sorted(new_tables.keys()-old_tables.keys())}')
        print(f'Deleted tables: {sorted(old_tables.keys()-new_tables.keys())}')
        for name in sorted(
                set(old_tables.keys()).intersection(set(new_tables.keys()))):
            TableComparer(
                args.max_diffs,
                old_tables[name],
                new_tables[name]).compare()


if __name__ == '__main__':
    try:
        main()
    except Exception as exception:
        logging.error(exception)
        raise exception
