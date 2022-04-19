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

GEO_FILENAME = os.path.join(INPUT_DIR, 'geography/geography.csv')

class TestCategory(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Category.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, GEO_FILENAME).categories

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

    def test_cats_for_geo_classification(self):
        row = REQUIRED_FIELDS.copy()
        row['Classification_Mnemonic'] = 'GEO1'
        self.run_test([row], f'^Reading {FILENAME}:2 found category for geographic classification GEO1: all categories for geographic classifications must be in a separate lookup file$')

    def test_cats_for_non_geo_var(self):
        read_data = """CLASS122CD,CLASS122NM,CLASS122NMW
CD1,NM1,NMW1
"""
        expected_error = f'^Reading {GEO_FILENAME}: found Welsh labels for non geographic classification: CLASS1$'
        with unittest.mock.patch('builtins.open', conditional_mock_open('geography.csv', read_data = read_data)):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, GEO_FILENAME).categories


if __name__ == '__main__':
    unittest.main()
