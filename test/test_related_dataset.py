import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Dataset_Mnemonic', 'Id', 'Related_Dataset_Mnemonic']

REQUIRED_FIELDS = {'Dataset_Mnemonic': 'DS1',
                   'Related_Dataset_Mnemonic': 'DS2',
                   'Id': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Related_Datasets.csv')

class TestRelatedDataset(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Related_Datasets.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR).load_dataset_to_related(['DS1', 'DS2', 'DS3'])

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_invalid_values(self):
        for field in ['Dataset_Mnemonic', 'Related_Dataset_Mnemonic']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_related_same_as_dataset(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Related_Dataset_Mnemonic': 'DS1', 'Id': '1'}],
            f'^Reading {FILENAME}:2 Dataset_Mnemonic is the same as Related_Dataset_Mnemonic: DS1$')

    def test_duplicate_entry(self):
        self.run_test(
                [{'Dataset_Mnemonic': 'DS1', 'Related_Dataset_Mnemonic': 'DS2', 'Id': '1'},
                 {'Dataset_Mnemonic': 'DS1', 'Related_Dataset_Mnemonic': 'DS3', 'Id': '2'},
                 {'Dataset_Mnemonic': 'DS1', 'Related_Dataset_Mnemonic': 'DS2', 'Id': '3'}],
            f'^Reading {FILENAME}:4 duplicate value combo DS2/DS1 for Related_Dataset_Mnemonic/Dataset_Mnemonic$')


if __name__ == '__main__':
    unittest.main()
