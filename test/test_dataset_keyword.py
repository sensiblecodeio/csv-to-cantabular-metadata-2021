import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Id', 'Dataset_Keyword', 'Dataset_Mnemonic']

REQUIRED_FIELDS = {'Dataset_Keyword': 'Keyword',
                   'Dataset_Mnemonic': 'DS1',
                   'Id': 1}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Dataset_Keyword.csv')

class TestDatasetKeyword(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Dataset_Keyword.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).load_dataset_keywords(['DS1'])

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_duplicate_records(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value combo Keyword/DS1 for Dataset_Keyword/Dataset_Mnemonic$')


if __name__ == '__main__':
    unittest.main()
