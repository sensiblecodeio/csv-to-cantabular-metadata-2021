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


Row = namedtuple('Row', 'data line_num')


class Reader:
    """Reader is used to read a CSV file containing metadata."""

    def __init__(self, filename, columns, id_column, unique_combo_fields=None):
        """Initialise Reader object."""
        self.filename = filename
        self.columns = columns
        self.expected_columns = {c.name for c in columns}
        self.unique_column_values = {c.name: set() for c in columns if c.unique}
        self.unique_combo_fields = unique_combo_fields
        if unique_combo_fields:
            self.unique_combos = set()
        self.id_column = id_column

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

            for row in reader:
                if None in row:
                    raise ValueError(f'Reading {self.filename}: too many fields on line '
                                     f'{reader.line_num}')
                if None in row.values():
                    raise ValueError(f'Reading {self.filename}: too few fields on line '
                                     f'{reader.line_num}')

                for k in list(row.keys()):
                    if k not in self.expected_columns:
                        del row[k]

                if not [k for k in row if row[k]]:
                    continue

                if not self.validate_row(row, reader.line_num):
                    logging.warning(f'dropping record at {self.filename} {self.id_column}: '
                                    f'{row[self.id_column]}')
                    continue

                for k in row.keys():
                    if row[k] == '':
                        row[k] = None

                data.append(Row(row, reader.line_num))

        return data



    def validate_row(self, row, line_num):
        """Validate the fields in a row."""
        keep_row = True

        def validation_error(msg):
            logging.warning(f'Reading {self.filename}:{line_num} {msg}')
            # raise ValueError(f'Reading {self.filename}:{line_num} {msg}')

        for column in self.columns:
            row[column.name] = row[column.name].strip()

            if column.required and not row[column.name]:
                validation_error(f'no value supplied for required field {column.name}')
                keep_row = False
                continue

            if column.unique:
                if row[column.name] in self.unique_column_values[column.name]:
                    validation_error(f'duplicate value {row[column.name]} for {column.name}')
                    keep_row = False
                    continue
                self.unique_column_values[column.name].add(row[column.name])

            if row[column.name] and column.validate_fn and not \
                    column.validate_fn(row[column.name]):
                validation_error(f'invalid value {row[column.name]} for {column.name}')
                if column.required:
                    keep_row = False
                    continue
                row[column.name] = ""

        if self.unique_combo_fields:
            combo = tuple([row[f] for f in self.unique_combo_fields])
            if combo in self.unique_combos:
                validation_error(f'duplicate value combo {"/".join(combo)} for '
                                 f'{"/".join(self.unique_combo_fields)}')
                keep_row = False
            self.unique_combos.add(combo)

        return keep_row
