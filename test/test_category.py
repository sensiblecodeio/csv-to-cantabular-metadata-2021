import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Source_Variable_Mnemonic', 'Classification_Mnemonic', 'Target_Variable_Mnemonic',
           'Id', 'Category_Code', 'Label', 'Label_Welsh', 'Sort_Order', 'Version']

REQUIRED_FIELDS = {'Category_Code': 'CODE1',
                   'Classification_Mnemonic': 'CLASS1',
                   'Label': 'label 1',
                   'Id': '1',
                   'Source_Variable_Mnemonic': 'source',
                   'Version': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Category.csv')

class TestCategory(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Category.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR).categories

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_invalid_values(self):
        for field in ['Classification_Mnemonic']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_wrong_number_categories(self):
        self.run_test(
            [REQUIRED_FIELDS],
            f'^Reading {FILENAME} Unexpected number of categories for CLASS1: expected 6 but found 1$')

    def test_duplicate_entry(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value combo CODE1/CLASS1 for Category_Code/Classification_Mnemonic$')


if __name__ == '__main__':
    unittest.main()
