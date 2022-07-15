import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Id', 'Database_Type_Code', 'Database_Type_Description']

REQUIRED_FIELDS = {'Database_Type_Code': 'DT',
                   'Database_Type_Description': 'DT description',
                   'Id': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Database_Type.csv')

class TestDatabaseType(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Database_Type.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).database_types

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_duplicate_database_type_code(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value DT for Database_Type_Code$')

    def test_missing_tabular_database_type(self):
        self.run_test(
            [{'Database_Type_Code': 'MICRODATA', 'Id': '1', 'Database_Type_Description': 'Microdata type'}],
            f'^AGGDATA not found as Database_Type_Code for any entry in {FILENAME}$')


if __name__ == '__main__':
    unittest.main()
