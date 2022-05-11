import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Classification_Mnemonic', 'Variable_Mnemonic', 'Id', 'External_Classification_Label_English',
           'External_Classification_Label_Welsh', 'Number_Of_Category_Items', 'Mnemonic_2011',
           'Flat_Classification_Flag', 'Parent_Classification_Mnemonic', 'Security_Mnemonic',
           'Signed_Off_Flag', 'Default_Classification_Flag', 'Version', 'Internal_Classification_Label_English']

REQUIRED_FIELDS = {'Classification_Mnemonic': 'CLASS1',
                   'Security_Mnemonic': 'PUB',
                   'Variable_Mnemonic': 'VAR1',
                   'Internal_Classification_Label_English': 'label',
                   'Version': '1',
                   'Id': '1',
                   'Signed_Off_Flag': 'N'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Classification.csv')

class TestClassification(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Classification.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).classifications

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_invalid_values(self):
        for field in ['Security_Mnemonic', 'Variable_Mnemonic', 'Number_Of_Category_Items',
                      'Signed_Off_Flag']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_duplicate_classification_mnemonic(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value CLASS1 for Classification_Mnemonic$')

    def test_non_public_variable(self):
        row = REQUIRED_FIELDS.copy()
        row['Variable_Mnemonic'] = 'VAR_PRIV'
        self.run_test([row], f'^Reading {FILENAME}:2 Public classification CLASS1 has non-public variable VAR_PRIV$')

    def test_geo_variable(self):
        row = REQUIRED_FIELDS.copy()
        row['Variable_Mnemonic'] = 'GEO1'
        self.run_test([row], f'^Reading {FILENAME}:2 CLASS1 has a geographic variable GEO1 which is not allowed$')


if __name__ == '__main__':
    unittest.main()
