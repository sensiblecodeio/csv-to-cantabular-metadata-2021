import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Security_Mnemonic', 'Id', 'Security_Description', 'Security_Description_Welsh']

REQUIRED_FIELDS = {'Security_Mnemonic': 'PUB',
                   'Id': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Security_Classification.csv')

class TestSecurityClassification(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Security_Classification.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR).security_classifications

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_duplicate_security_mnemonic(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value PUB for Security_Mnemonic$')

    def test_missing_public_security_classification(self):
        self.run_test(
            [{'Security_Mnemonic': 'PRIVATE', 'Id': '1'}],
            f'^PUB not found as Security_Mnemonic for any entry in {FILENAME}$')


if __name__ == '__main__':
    unittest.main()
