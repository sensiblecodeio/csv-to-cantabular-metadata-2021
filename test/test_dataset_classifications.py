import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Classification_Mnemonic', 'Dataset_Mnemonic', 'Id', 'Processing_Priority', 'Version']

REQUIRED_FIELDS = {'Dataset_Mnemonic': 'DS1',
                   'Classification_Mnemonic': 'CLASS1',
                   'Processing_Priority': '1',
                   'Version': '1',
                   'Id': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Dataset_Classification.csv')

class TestDatasetClassification(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Dataset_Classification.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR).load_dataset_to_classifications(['DS1', 'DS2', 'DS3'])

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_invalid_values(self):
        for field in ['Dataset_Mnemonic', 'Classification_Mnemonic', 'Processing_Priority']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_duplicate_entry(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value combo DS1/CLASS1 for Dataset_Mnemonic/Classification_Mnemonic')

    def test_invalid_processing_priority_set1(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Classification_Mnemonic': 'CLASS1',
              'Processing_Priority': '1', 'Version': '1', 'Id': '1'},
             {'Dataset_Mnemonic': 'DS1', 'Classification_Mnemonic': 'CLASS2',
              'Processing_Priority': '1', 'Version': '1', 'Id': '1'}],
            f'^Reading {FILENAME} Invalid processing_priorities \[1, 1\] for dataset DS1$')

    def test_invalid_processing_priority_set2(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Classification_Mnemonic': 'CLASS1',
              'Processing_Priority': '2', 'Version': '1', 'Id': '1'},
             {'Dataset_Mnemonic': 'DS1', 'Classification_Mnemonic': 'CLASS2',
              'Processing_Priority': '3', 'Version': '1', 'Id': '1'}],
            f'^Reading {FILENAME} Invalid processing_priorities \[2, 3\] for dataset DS1$')


if __name__ == '__main__':
    unittest.main()
