import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Classification_Mnemonic', 'Dataset_Mnemonic', 'Id', 'Processing_Priority',
           'Variable_Mnemonic', 'Lowest_Geog_Variable_Flag']

REQUIRED_FIELDS = {'Dataset_Mnemonic': 'DS1',
                   'Variable_Mnemonic': 'VAR1',
                   'Id': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Dataset_Variable.csv')

class TestDatasetClassification(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Dataset_Variable.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).load_dataset_to_variables(['DS1', 'DS2', 'DS3'])

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_invalid_values(self):
        for field in ['Dataset_Mnemonic', 'Classification_Mnemonic', 'Processing_Priority',
                      'Lowest_Geog_Variable_Flag']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_duplicate_entry(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value combo DS1/VAR1 for Dataset_Mnemonic/Variable_Mnemonic')

    def test_invalid_processing_priority_set1(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Classification_Mnemonic': 'CLASS1',
              'Processing_Priority': '1', 'Id': '1', 'Variable_Mnemonic': 'VAR1'},
             {'Dataset_Mnemonic': 'DS1', 'Classification_Mnemonic': 'CLASS2',
              'Processing_Priority': '1', 'Id': '1', 'Variable_Mnemonic': 'VAR2'}],
            f'^Reading {FILENAME} Invalid processing_priorities \[1, 1\] for dataset DS1$')

    def test_invalid_processing_priority_set2(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Classification_Mnemonic': 'CLASS1',
              'Processing_Priority': '2', 'Id': '1', 'Variable_Mnemonic': 'VAR1'},
             {'Dataset_Mnemonic': 'DS1', 'Classification_Mnemonic': 'CLASS2',
              'Processing_Priority': '3', 'Id': '1', 'Variable_Mnemonic': 'VAR2'}],
            f'^Reading {FILENAME} Invalid processing_priorities \[2, 3\] for dataset DS1$')

    def test_classification_on_geo_var(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Variable_Mnemonic': 'GEO1',
              'Id': '1', 'Classification_Mnemonic': 'GEO1'}],
            f'^Reading {FILENAME}:2 Classification_Mnemonic must not be specified for geographic variable GEO1 in dataset DS1$')

    def test_processing_priority_on_geo_var(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Variable_Mnemonic': 'GEO1',
              'Id': '1', 'Processing_Priority': '1'}],
            f'^Reading {FILENAME}:2 Processing_Priority must not be specified for geographic variable GEO1 in dataset DS1$')

    def test_no_classification_on_non_geo_var(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Variable_Mnemonic': 'VAR1',
              'Id': '1', 'Processing_Priority': '1'}],
            f'^Reading {FILENAME}:2 Classification must be specified for non-geographic VAR1 in dataset DS1$')

    def test_no_processing_priority_on_non_geo_var(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Variable_Mnemonic': 'VAR1',
              'Id': '1', 'Classification_Mnemonic': 'CLASS1'}],
            f'^Reading {FILENAME}:2 Processing_Priority not specified for classification CLASS1 in dataset DS1$')

    def test_lowest_geog_on_non_geo_var(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Variable_Mnemonic': 'VAR1',
              'Id': '1', 'Classification_Mnemonic': 'CLASS1', 'Processing_Priority': '1',
              'Lowest_Geog_Variable_Flag': 'Y'}],
            f'^Reading {FILENAME}:2 Lowest_Geog_Variable_Flag set on non-geographic variable VAR1 for dataset DS1$')

    def test_invalid_classification_on_var(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Variable_Mnemonic': 'VAR1',
              'Id': '1', 'Classification_Mnemonic': 'CLASS2', 'Processing_Priority': '1'}],
            f'^Reading {FILENAME}:2 Invalid classification CLASS2 specified for variable VAR1 in dataset DS1$')

    def test_no_lowest_geog_flag(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Variable_Mnemonic': 'GEO1',
              'Id': '1'}],
            f'^Reading {FILENAME} Lowest_Geog_Variable_Flag not set on any geographic variables for dataset DS1$')

    def test_duplicate_lowest_geog_flag(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Variable_Mnemonic': 'GEO1',
              'Id': '1', 'Lowest_Geog_Variable_Flag': 'Y'},
             {'Dataset_Mnemonic': 'DS1', 'Variable_Mnemonic': 'GEO2',
              'Id': '1', 'Lowest_Geog_Variable_Flag': 'Y'}],
            f'^Reading {FILENAME}:3 Lowest_Geog_Variable_Flag set on variable GEO2 and GEO1 for dataset DS1$')


if __name__ == '__main__':
    unittest.main()
