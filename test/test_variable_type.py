import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Variable_Type_Code', 'Id', 'Variable_Type_Description', 'Variable_Type_Description_Welsh']

REQUIRED_FIELDS = {'Variable_Type_Code': 'GEOG',
                   'Variable_Type_Description': 'description',
                   'Id': 1}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Variable_Type.csv')

class TestVariableType(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Variable_Type.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).variable_types

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_duplicate_variable_type_code(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value GEOG for Variable_Type_Code$')

    def test_missing_geographic_variable_type(self):
        self.run_test(
                [{'Variable_Type_Code': 'DVO', 'Variable_Type_Description': 'description', 'Id': '1'}],
            f'^GEOG not found as Variable_Type_Code for any entry in {FILENAME}$')


if __name__ == '__main__':
    unittest.main()
