"""Load metadata from CSV files and export in JSON format."""
import csv
import logging
from collections import namedtuple

Column = namedtuple('Column', 'name unique validate_fn required')


def required(name, unique=False, validate_fn=None):
    """Return a Column with required set to True."""
    return Column(name, unique, validate_fn, required=True)


def optional(name, unique=False, validate_fn=None):
    """Return a Column with required set to False."""
    return Column(name, unique, validate_fn, required=False)


Row = namedtuple('Row', 'data row_num')


class Reader:
    """Reader is used to read a CSV file containing metadata."""

    def __init__(self, filename, columns, recoverable_error, unique_combo_fields=None):
        """Initialise Reader object."""
        self.filename = filename
        self.columns = columns
        self.expected_columns = {c.name for c in columns}
        self.unique_column_values = {c.name: set() for c in columns if c.unique}
        self.unique_combo_fields = unique_combo_fields
        if unique_combo_fields:
            self.unique_combos = set()
        self.recoverable_error = recoverable_error

    def read(self):
        """
        Read a file as a dictionary with each value corresponding to a list of rows.

        Each row is converted to a dictionary, and added to the returned dictionary using the "key"
        field in the row as a key.
        """
        data = []
        with open(self.filename, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            header_set = set(reader.fieldnames)

            missing_columns = self.expected_columns - header_set
            if missing_columns:
                raise ValueError(f'Reading {self.filename}: missing expected columns: '
                                 f'{", ".join(sorted(missing_columns))}')

            for row_num, row in enumerate(reader, 2):
                if None in row:
                    raise ValueError(f'Reading {self.filename}: too many fields on row {row_num}')
                if None in row.values():
                    raise ValueError(f'Reading {self.filename}: too few fields on row {row_num}')

                for k in list(row.keys()):
                    if k not in self.expected_columns:
                        del row[k]

                if not [k for k in row if row[k]]:
                    continue

                if not self.validate_row(row, row_num):
                    logging.warning(f'Reading {self.filename}:{row_num} dropping record')
                    continue

                for k in row.keys():
                    if row[k] == '':
                        row[k] = None

                data.append(Row(row, row_num))

        return data

    def validate_row(self, row, row_num):
        """Validate the fields in a row."""
        keep_row = True
        for column in self.columns:
            row[column.name] = row[column.name].strip()

            if column.required and not row[column.name]:
                self.recoverable_error(f'Reading {self.filename}:{row_num} no value supplied '
                                       f'for required field {column.name}')
                keep_row = False
                continue

            if column.unique:
                if row[column.name] in self.unique_column_values[column.name]:
                    self.recoverable_error(f'Reading {self.filename}:{row_num} duplicate '
                                           f'value {row[column.name]} for {column.name}')
                    keep_row = False
                    continue

                self.unique_column_values[column.name].add(row[column.name])

            if row[column.name] and column.validate_fn and not \
                    column.validate_fn(row[column.name]):
                self.recoverable_error(f'Reading {self.filename}:{row_num} invalid value '
                                       f'{row[column.name]} for {column.name}')
                if column.required:
                    keep_row = False
                    continue
                logging.warning(f'Reading {self.filename}:{row_num} ignoring field {column.name}')
                row[column.name] = ""

        if self.unique_combo_fields and keep_row:
            combo = tuple([row[f] for f in self.unique_combo_fields])
            if combo in self.unique_combos:
                self.recoverable_error(f'Reading {self.filename}:{row_num} duplicate '
                                       f'value combo {"/".join(combo)} for '
                                       f'{"/".join(self.unique_combo_fields)}')

                keep_row = False
            else:
                self.unique_combos.add(combo)

        return keep_row
