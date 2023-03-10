import unittest.mock
import unittest
import os
import pathlib
from ons_csv_to_ctb_json_load import Loader
from helper_funcs import conditional_mock_open, build_test_file

HEADERS = ['Variable_Mnemonic', 'Id', 'Variable_Title', 'Variable_Title_Welsh',
           'Variable_Description', 'Variable_Description_Welsh', 'Variable_Type_Code',
           'Statistical_Unit', 'Topic_Mnemonic', 'Variable_Mnemonic_2011',
           'Comparability_Comments', 'Comparability_Comments_Welsh', 'Uk_Comparison_Comments',
           'Uk_Comparison_Comments_Welsh', 'Security_Mnemonic', 'Signed_Off_Flag',
           'Number_Of_Classifications', 'Geography_Hierarchy_Order',
           'Geographic_Theme', 'Geographic_Theme_Welsh', 'Geographic_Coverage',
           'Geographic_Coverage_Welsh', 'Version', 'Quality_Statement_Text', 
           'Quality_Statement_Text_Welsh', 'Quality_Summary_URL',
           'Variable_Short_Description', 'Variable_Short_Description_Welsh']

COMMON_FIELDS = {'Security_Mnemonic': 'PUB',
                 'Variable_Title': 'title',
                 'Variable_Description': 'description',
                 'Id': '1',
                 'Version': '1',
                 'Signed_Off_Flag': 'N'}

REQUIRED_FIELDS = {'Variable_Mnemonic': 'VAR1',
                   'Variable_Type_Code': 'DVO',
                   **COMMON_FIELDS}

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), 'testdata')

FILENAME = os.path.join(INPUT_DIR, 'Variable.csv')

class TestVariable(unittest.TestCase):
    def run_test(self, rows, expected_error):
        with unittest.mock.patch('builtins.open', conditional_mock_open('Variable.csv',
                read_data = build_test_file(HEADERS, rows))):
            with self.assertRaisesRegex(ValueError, expected_error):
                Loader(INPUT_DIR, None).variables

    def test_required_fields(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = ''
                self.run_test([row], f'^Reading {FILENAME}:2 no value supplied for required field {field}$')

    def test_invalid_values(self):
        for field in ['Security_Mnemonic', 'Variable_Type_Code', 'Statistical_Unit', 'Topic_Mnemonic',
                      'Signed_Off_Flag']:
            with self.subTest(field=field):
                row = REQUIRED_FIELDS.copy()
                row[field] = 'X'
                self.run_test([row], f'^Reading {FILENAME}:2 invalid value X for {field}$')

    def test_duplicate_variable_mnemonic(self):
        self.run_test(
            [REQUIRED_FIELDS, REQUIRED_FIELDS],
            f'^Reading {FILENAME}:3 duplicate value VAR1 for Variable_Mnemonic$')

    def test_non_geo_with_geographic_value(self):
        for field in ['Geographic_Theme', 'Geographic_Theme_Welsh',
                      'Geographic_Coverage', 'Geographic_Coverage_Welsh', 'Geography_Hierarchy_Order']:
            with self.subTest(field=field):
                rows = [{'Variable_Mnemonic': 'GEO1', 'Variable_Type_Code': 'GEOG', 'Geography_Hierarchy_Order': '1',
                         **COMMON_FIELDS},
                        {'Variable_Mnemonic': 'VAR2', 'Variable_Type_Code': 'DVO', **COMMON_FIELDS},
                        {'Variable_Mnemonic': 'VAR1', 'Variable_Type_Code': 'DVO', **COMMON_FIELDS,
                         field: '1'}]
                self.run_test(rows, f'^Reading {FILENAME}:4 {field} specified for non geographic variable: VAR1$')

    def test_geo_with_missing_fields(self):
        for field in ['Geography_Hierarchy_Order']:
            with self.subTest(field=field):
                rows = [{'Variable_Mnemonic': 'GEO1', 'Variable_Type_Code': 'GEOG', 'Geography_Hierarchy_Order': '1',
                         'Geographic_Theme': 'GEO1 Theme', 'Geographic_Coverage': 'GEO1 Coverage', **COMMON_FIELDS},
                        {'Variable_Mnemonic': 'VAR1', 'Variable_Type_Code': 'DVO', **COMMON_FIELDS}]
                rows[0].pop(field)
                self.run_test(rows, f'^Reading {FILENAME}:2 no {field} specified for geographic variable: GEO1$')

    def test_duplicate_geo_hierarchy(self):
        rows = [{'Variable_Mnemonic': 'GEO1', 'Variable_Type_Code': 'GEOG', 'Geography_Hierarchy_Order': '1',
                 'Geographic_Theme': 'GEO1 Theme', 'Geographic_Coverage': 'GEO1 Coverage', **COMMON_FIELDS},
                {'Variable_Mnemonic': 'GEO2', 'Variable_Type_Code': 'GEOG', 'Geography_Hierarchy_Order': '1',
                 'Geographic_Theme': 'GEO2 Theme', 'Geographic_Coverage': 'GEO2 Coverage', **COMMON_FIELDS},
                        {'Variable_Mnemonic': 'VAR1', 'Variable_Type_Code': 'DVO', **COMMON_FIELDS}]
        self.run_test(rows, f'^Reading {FILENAME}:3 Geography_Hierarchy_Order value of 1 specified for both GEO2 and GEO1$')


if __name__ == '__main__':
    unittest.main()
