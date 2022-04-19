import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Question_Code', 'Id', 'Question_Label', 'Question_Label_Welsh',
           'Reason_For_Asking_Question', 'Reason_For_Asking_Question_Welsh',
           'Question_First_Asked_In_Year', 'Version']

REQUIRED_FIELDS = {'Question_Code': 'Q1',
                   'Question_Label': 'label 1',
                   'Id': '1',
                   'Version': '1'}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Question.csv')

class TestQuestion(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Question.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).questions

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_duplicate_question_code(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value Q1 for Question_Code$')


if __name__ == '__main__':
    unittest.main()
