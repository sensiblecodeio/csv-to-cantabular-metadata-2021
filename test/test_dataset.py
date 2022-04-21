import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Dataset_Mnemonic', 'Id', 'Dataset_Title', 'Dataset_Title_Welsh', 'Dataset_Description',
           'Dataset_Description_Welsh', 'Statistical_Unit', 'Dataset_Mnemonic_2011',
           'Geographic_Coverage', 'Geographic_Coverage_Welsh', 'Dataset_Population',
           'Dataset_Population_Welsh', 'Dissemination_Source', 'Release_Frequency', 'Last_Updated',
           'Unique_Url', 'Security_Mnemonic', 'Signed_Off_Flag', 'Database_Mnemonic', 'Contact_Id',
           'Version']

COMMON_FIELDS = {'Dataset_Title': 'title',
                 'Dataset_Description': 'description',
                 'Geographic_Coverage': 'coverage',
                 'Dataset_Population': 'population',
                 'Id': '1',
                 'Statistical_Unit': 'People',
                 'Version': '1'}

REQUIRED_FIELDS = {'Dataset_Mnemonic': 'DS1',
                   'Database_Mnemonic': 'DB1',
                   'Security_Mnemonic': 'PUB',
                   **COMMON_FIELDS}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Dataset.csv')

class TestDataset(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Dataset.csv',
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
        for field in ['Security_Mnemonic', 'Database_Mnemonic', 'Contact_Id', 'Statistical_Unit']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_duplicate_dataset_mnemonic(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS1', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS}],
            f'^Reading {FILENAME}:3 duplicate value DS1 for Dataset_Mnemonic$')

    def test_private_classification(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS_PRIV', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS1', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS2', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS3', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS4', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS}],
            f'^Reading {FILENAME}:2 Public ONS dataset DS_PRIV has non-public classification CLASS_PRIV$')

    def test_variable_not_in_database(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Database_Mnemonic': 'DB2', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS_PRIV', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'CLASS', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS2', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS3', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS4', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS}],
            f'^Reading {FILENAME}:2 DS1 has classification GEO1 that is not in database DB2$')

    def test_no_variables(self):
        self.run_test(
            [{'Dataset_Mnemonic': 'DS1', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS_PRIV', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'CLASS', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS2', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS3', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS4', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS},
             {'Dataset_Mnemonic': 'DS5', 'Database_Mnemonic': 'DB1', 'Security_Mnemonic': 'PUB', **COMMON_FIELDS}],
            f'^Reading {FILENAME}:7 DS5 has no associated classifications or geographic variable$')


if __name__ == '__main__':
    unittest.main()
