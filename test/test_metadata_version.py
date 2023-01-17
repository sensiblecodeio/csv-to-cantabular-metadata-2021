import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Metadata_Version_Number', 'Id']

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Metadata_Version.csv')

class TestMetadataVersion(unittest.TestCase):
    def run_test_value(self, rows, expected_value):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Metadata_Version.csv',
                read_data = build_test_file(HEADERS, rows))):
            self.assertEqual(expected_value, Loader(INPUT_DIR, None).metadata_version_number)

    def test_no_values(self):
        self.run_test_value([], '')

    def test_last_value(self):
        self.run_test_value([{'Id': '1', 'Metadata_Version_Number': '10'},
                             {'Id': '2', 'Metadata_Version_Number': '20'},
                             {'Id': '3', 'Metadata_Version_Number': '30'}], '30')

    def test_duplicate_values(self):
        self.run_test_value([{'Id': '1', 'Metadata_Version_Number': '3'},
                             {'Id': '2', 'Metadata_Version_Number': '3'}], '3')

    def test_empty_values(self):
        self.run_test_value([{'Id': '1', 'Metadata_Version_Number': ''},
                             {'Id': '', 'Metadata_Version_Number': '20'}], '20')


if __name__ == '__main__':
    unittest.main()
