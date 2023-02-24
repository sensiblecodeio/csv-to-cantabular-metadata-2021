"""Access metadata from CSV source files."""

import csv
import os


class SourceMetadata:
    """Class to provide information on metadata from files in CSV format."""

    def __init__(self, metadata_dir):
        """Initialise SourceMetadata."""
        self.metadata_dir = metadata_dir

    def _open_file(self, filename):
        return open(os.path.join(self.metadata_dir, filename), encoding='utf-8')

    def _get_csv_column_values(self, filename, column):
        values = set()
        with self._open_file(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                value = row[column].strip()
                if value:
                    values.add(value)

        return tuple(sorted(list(values)))

    def variables(self):
        """Identify all the Cantabular variables from a set of CSV metadata files."""
        # Cantabular variable names are the set of Codebook_Mnemonic values from
        # Category_Mapping.csv along with the Variable_Mnemonic values from Variable.csv for
        # geographic variables.
        non_geog_variables = self._get_csv_column_values('Category_Mapping.csv',
                                                         'Codebook_Mnemonic')

        variables = set(non_geog_variables)
        with self._open_file('Variable.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                variable_mnemonic = row['Variable_Mnemonic'].strip()
                if variable_mnemonic and row['Variable_Type_Code'].strip() == 'GEOG':
                    variables.add(variable_mnemonic)

        return tuple(sorted(list(variables)))

    def datasets(self):
        """Identify all the Cantabular datasets from a set of CSV metadata files."""
        return self._get_csv_column_values('Database.csv', 'Database_Mnemonic')

    def tables(self):
        """Identify all the Cantabular tables from a set of CSV metadata files."""
        return self._get_csv_column_values('Dataset.csv', 'Dataset_Mnemonic')
