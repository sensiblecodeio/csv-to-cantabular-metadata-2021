import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Id', 'Database_Mnemonic', 'Variable_Mnemonic', 'Version']

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
                input_dir = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')
                Loader(input_dir).database_to_classifications

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


if __name__ == '__main__':
    unittest.main()
