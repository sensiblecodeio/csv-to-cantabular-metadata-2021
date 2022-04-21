import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Id', 'Database_Mnemonic', 'Variable_Mnemonic', 'Version', 'Lowest_Geog_Variable_Flag']

REQUIRED_FIELDS = {'Variable_Mnemonic': 'VAR1',
                   'Database_Mnemonic': 'DB1',
                   'Id': '1',
                   'Version': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Database_Variable.csv')


class TestDatabaseVariable(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Database_Variable.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).load_database_to_variables(['DB1', 'DB2', 'DB3'])

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_invalid_values(self):
        for field in ['Variable_Mnemonic', 'Database_Mnemonic']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_duplicate_entry(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value combo VAR1/DB1 for Variable_Mnemonic/Database_Mnemonic$')

    def test_lowest_geog_on_non_geo_var(self):
        row = REQUIRED_FIELDS.copy()
        row['Lowest_Geog_Variable_Flag'] = 'Y'
        self.run_test(
            [row],
            f'^Reading {FILENAME} Lowest_Geog_Variable_Flag set on non-geographic variable VAR1 for database DB1$')

    def test_duplicate_lowest_geog(self):
        self.run_test([{'Variable_Mnemonic': 'GEO1', 'Database_Mnemonic': 'DB1', 'Id': '1',
                        'Version': '1', 'Lowest_Geog_Variable_Flag': 'Y'},
                       {'Variable_Mnemonic': 'GEO2', 'Database_Mnemonic': 'DB1', 'Id': '1',
                        'Version': '1', 'Lowest_Geog_Variable_Flag': 'Y'}],
            f'^Reading {FILENAME} Lowest_Geog_Variable_Flag set on GEO2 and GEO1 for database DB1$')

    def test_no_lowest_geog_var(self):
        row = REQUIRED_FIELDS.copy()
        row['Variable_Mnemonic'] = 'GEO1'
        self.run_test(
            [row],
            f'^Reading {FILENAME} Lowest_Geog_Variable_Flag not set on any geographic variable for database DB1$')

if __name__ == '__main__':
    unittest.main()
