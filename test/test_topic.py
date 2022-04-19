import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Topic_Mnemonic', 'Id', 'Topic_Description', 'Topic_Description_Welsh', 'Topic_Title',
           'Topic_Title_Welsh']

REQUIRED_FIELDS = {'Topic_Mnemonic': 'TOPIC1',
                   'Topic_Title': 'title',
                   'Topic_Description': 'description',
                   'Id': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Topic.csv')

class TestTopic(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Topic.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).topics

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_duplicate_topic_mnemonic(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value TOPIC1 for Topic_Mnemonic$')


if __name__ == '__main__':
    unittest.main()
