import json
import unittest.mock
import unittest
import pathlib
import os
import logging
from io import StringIO
import remove_empty_rows_and_columns

FILENAME_TEST1 = 'empty_rows_and_columns_test1.csv'
FILENAME_TEST2 = 'empty_rows_and_columns_test2.csv'


class TestRemoveEmptyRowsAndColumns(unittest.TestCase):
    def test_modified_remove_empty_rows_and_columns(self):
        """Generate transformed source CSV and compare it with expected values."""
        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata/empty_rows_and_columns')
        output_dir = os.path.join(file_dir, 'out')

        with self.assertLogs() as cm:
            with unittest.mock.patch('sys.argv',
                    ['test', '--force-overwrite', '-i', input_dir, '-o', output_dir]):
                remove_empty_rows_and_columns.main()
                with open(os.path.join(output_dir, FILENAME_TEST1)) as f:
                    fOut = f.read()
                with open(os.path.join(file_dir, f'expected/{FILENAME_TEST1}')) as f:
                    fExpected = f.read()
                self.assertEqual(fOut, fExpected,
                                 msg=f'Comparing out/{FILENAME_TEST1} and expected/{FILENAME_TEST1}')

                with open(os.path.join(output_dir, FILENAME_TEST2)) as f:
                    fOut = f.read()
                with open(os.path.join(file_dir, f'expected/{FILENAME_TEST2}')) as f:
                    fExpected = f.read()
                self.assertEqual(fOut, fExpected,
                                 msg=f'Comparing out/{FILENAME_TEST2} and expected/{FILENAME_TEST2}')

        logs = [

            r'empty_rows_and_columns_test2.csv\': removed 0 columns and 0 rows',
            r'empty_rows_and_columns_test1.csv\':2 extra data in cell 3: "4"',
            r'empty_rows_and_columns_test1.csv\':2 extra data in cell 4: "5"',
            r'empty_rows_and_columns_test1.csv\':2 extra data in cell 5: "6"',
            r'empty_rows_and_columns_test1.csv\':6 too few cells on row: expected 3 but found 1',
            r'empty_rows_and_columns_test1.csv\':8 extra data in cell 3: "d"',
            r'empty_rows_and_columns_test1.csv\':8 extra data in cell 4: "e"',
            r'empty_rows_and_columns_test1.csv\':8 extra data in cell 5: "f"',
            r'empty_rows_and_columns_test1.csv\':11 extra data in cell 3: "D"',
            r'empty_rows_and_columns_test1.csv\':11 extra data in cell 4: "E"',
            r'empty_rows_and_columns_test1.csv\':11 extra data in cell 5: "F"',
            r'empty_rows_and_columns_test1.csv\': removed 3 columns and 6 rows'
        ]

        self.assertEqual(len(logs), len(cm.output))
        for i, warning in enumerate(cm.output):
            self.assertRegex(warning, logs[i])
