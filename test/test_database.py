import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Database_Mnemonic', 'Id', 'Database_Title', 'Database_Title_Welsh',
           'Database_Description', 'Database_Description_Welsh', 'Cantabular_DB_Flag',
           'IAR_Asset_Id', 'Source_Mnemonic', 'Version', 'Database_Type_Code']

REQUIRED_FIELDS = {'Database_Mnemonic': 'DB1',
                   'Source_Mnemonic': 'SRC1',
                   'Database_Title': 'title',
                   'Id': '1',
                   'Database_Description': 'description',
                   'Version': '1',
                   'Database_Type_Code': 'MICRO'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Database.csv')

class TestDatabase(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Database.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).databases

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_invalid_values(self):
        for field in ['Source_Mnemonic', 'Database_Type_Code']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_duplicate_database_mnemonic(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value DB1 for Database_Mnemonic$')


if __name__ == '__main__':
    unittest.main()
