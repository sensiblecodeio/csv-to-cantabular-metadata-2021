import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Source_Mnemonic', 'Id', 'Source_Description', 'Source_Description_Welsh',
           'Copyright_Statement', 'Licence', 'Nationals_Statistic_Certified', 'Methodology_Link',
           'Methodology_Statement', 'Methodology_Statement_Welsh', 'SDC_Link', 'SDC_Statement',
           'SDC_Statement_Welsh', 'Contact_Id', 'Version']

REQUIRED_FIELDS = {'Source_Mnemonic': 'SRC1',
                   'Source_Description': 'description',
                   'Id': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Source.csv')

class TestSource(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Source.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).sources

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_invalid_values(self):
        for field in ['Contact_Id']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_duplicate_source_mnemonic(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value SRC1 for Source_Mnemonic$')


if __name__ == '__main__':
    unittest.main()
