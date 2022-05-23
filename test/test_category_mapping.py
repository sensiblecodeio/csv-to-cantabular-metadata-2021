import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Classification_Mnemonic', 'Codebook_Mnemonic']

REQUIRED_FIELDS = {'Classification_Mnemonic': 'CLASS1',
                   'Codebook_Mnemonic': 'CLASS1 (Codebook)'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Category_Mapping.csv')

class TestCategoryMapping(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Category_Mapping.csv',
                read_data = build_test_file(HEADERS,rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).datasets

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

    def test_invalid_codebook_mnemonic(self):
        self.run_test(
            [{'Classification_Mnemonic': 'CLASS1', 'Codebook_Mnemonic': 'CLASS2'}],
            f'^Reading {FILENAME}:2 CLASS2 is an invalid Codebook_Mnemonic for classification CLASS1 as it is already the Classification_Mnemonic for another classification$')

    def test_different_codebook_mnemonics(self):
        self.run_test(
            [{'Classification_Mnemonic': 'CLASS1', 'Codebook_Mnemonic': 'CLASS1 (Codebook)'},
             {'Classification_Mnemonic': 'CLASS1', 'Codebook_Mnemonic': 'CLASS1 (Codebook 2)'}],
            f'^Reading {FILENAME}:3 different Codebook_Mnemonic values specified for classification CLASS1: CLASS1 \(Codebook 2\) and CLASS1 \(Codebook\)$')

    def test_different_codebook_mnemonics(self):
        self.run_test(
            [{'Classification_Mnemonic': 'CLASS1', 'Codebook_Mnemonic': 'CLASS1 (Codebook)'},
             {'Classification_Mnemonic': 'CLASS2', 'Codebook_Mnemonic': 'CLASS1 (Codebook)'}],
            f'^Reading {FILENAME}:3 CLASS1 \(Codebook\) is Codebook_Mnemonic for both CLASS1 and CLASS2$')


if __name__ == '__main__':
    unittest.main()
