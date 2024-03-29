import json
import unittest.mock
import unittest
import pathlib
import os
import logging
from io import StringIO
from datetime import datetime
import ons_csv_to_ctb_json_main

FILENAME_TABLES = 'cantabm_v10-2-3_best-effort_tables-md_19700101-1.json'
FILENAME_DATASET = 'cantabm_v10-2-3_best-effort_dataset-md_19700101-1.json'
FILENAME_SERVICE = 'cantabm_v10-2-3_best-effort_service-md_19700101-1.json'

class TestBestEffort(unittest.TestCase):
    @unittest.mock.patch('ons_csv_to_ctb_json_main.datetime')
    def test_generated_json_best_effort(self, mock_datetime):
        """Generate JSON from source CSV and compare it with expected values."""
        mock_datetime.now.return_value = datetime(1970, 1, 1)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata/best_effort')
        output_dir = os.path.join(file_dir, 'out')

        with self.assertLogs(level='INFO') as cm:
            with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir, '-m', 'best-effort', '--best-effort']):
                ons_csv_to_ctb_json_main.main()
                with open(os.path.join(output_dir, FILENAME_SERVICE)) as f:
                    service_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/service-metadata-best-effort.json')) as f:
                    expected_service_metadata = json.load(f)
                self.assertEqual(service_metadata, expected_service_metadata,
                                 msg=f'Comparing out/{FILENAME_SERVICE} and expected/service-metadata-best-effort.json')

                with open(os.path.join(output_dir, FILENAME_DATASET)) as f:
                    dataset_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/dataset-metadata-best-effort.json')) as f:
                    expected_dataset_metadata = json.load(f)
                self.assertEqual(dataset_metadata, expected_dataset_metadata,
                                 msg=f'Comparing out/{FILENAME_DATASET} and expected/dataset-metadata-best-effort.json')

                with open(os.path.join(output_dir, FILENAME_TABLES)) as f:
                    table_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/table-metadata-best-effort.json')) as f:
                    expected_table_metadata = json.load(f)
                self.assertEqual(table_metadata, expected_table_metadata,
                                 msg=f'Comparing out/{FILENAME_TABLES} and expected/table-metadata-best-effort.json')

        exp_warnings = [
            r'Variable.csv:4 Geography_Hierarchy_Order value of 10 specified for both GEO2 and GEO1',
            r'Variable.csv:8 no Geography_Hierarchy_Order specified for geographic variable: GEO4',
            r'Variable.csv:8 using 0 for Geography_Hierarchy_Order',
            r'Classification.csv:3 no value supplied for required field Variable_Mnemonic',
            r'Classification.csv:3 dropping record',
            r'Classification.csv:4 duplicate value CLASS1 for Classification_Mnemonic',
            r'Classification.csv:4 dropping record',
            r'Classification.csv:5 invalid value x for Number_Of_Category_Items',
            r'Classification.csv:5 ignoring field Number_Of_Category_Items',
            r'Category_Mapping.csv:3 different Codebook_Mnemonic values specified for classification CLASS1: CLASS1 \(Codebook A\) and CLASS1 \(Codebook\)',
            r'Category_Mapping.csv:4 CLASS1 \(Codebook\) is Codebook_Mnemonic for both CLASS1 and CLASS3',
            r'Category_Mapping.csv:4 ignoring field Codebook_Mnemonic',
            r'Category_Mapping.csv:5 CLASS1 is an invalid Codebook_Mnemonic for classification CLASS4 as it is already the Classification_Mnemonic for another classification',
            r'Category_Mapping.csv:5 ignoring field Codebook_Mnemonic',
            r'Category.csv Unexpected number of categories for CLASS1: expected 4 but found 1',
            r'Database_Variable.csv Lowest_Geog_Variable_Flag set on GEO3 and GEO1 for database DB1',
            r'Database_Variable.csv GEO1 is unknown Classification_Mnemonic for Variable_Mnemonic VAR1',
            r'Dataset_Variable.csv:4 duplicate value combo DS1/VAR1 for Dataset_Mnemonic/Variable_Mnemonic',
            r'Dataset_Variable.csv:4 dropping record',
            r'Dataset_Variable.csv:2 Lowest_Geog_Variable_Flag set on non-geographic variable VAR1 for dataset DS1',
            r'Dataset_Variable.csv:2 Processing_Priority not specified for classification CLASS1 in dataset DS1',
            r'Dataset_Variable.csv:2 using 0 for Processing_Priority',
            r'Dataset_Variable.csv:3 Classification_Mnemonic must not be specified for geographic variable GEO1 in dataset DS1',
            r'Dataset_Variable.csv:3 Processing_Priority must not be specified for geographic variable GEO1 in dataset DS1',
            r'Dataset_Variable.csv:5 Lowest_Geog_Variable_Flag set on variable GEO2 and GEO1 for dataset DS1',
            r'Dataset_Variable.csv:5 DS1 has geographic variable GEO2 that is not in database DB1',
            r'Dataset_Variable.csv:7 Classification must be specified for non-geographic VAR2 in dataset DS1',
            r'Dataset_Variable.csv:7 dropping record',
            r'Dataset_Variable.csv:8 Invalid classification CLASS1 specified for variable VAR3 in dataset DS1',
            r'Dataset_Variable.csv:8 dropping record',
            r'Dataset_Variable.csv:9 DS2 has classification CLASS3 that is not in database DB1',
            r'Dataset_Variable.csv:10 DS4 has Database_Mnemonic DB_TAB which has invalid Database_Type_Code: AGGDATA',
            r'Dataset_Variable.csv Invalid processing_priorities \[0\] for dataset DS1',
            r'Dataset.csv:4 DS3 has no associated classifications or geographic variable',
            r'Dataset.csv:4 dropping record',
            r"Dataset.csv:5 DS4 has an empty value for Destination_Pre_Built_Database_Mnemonic and has classifications from multiple databases: \['DB2', 'DB_TAB']",
            r'Dataset.csv:6 DS5 has Destination_Pre_Built_Database_Mnemonic DB1 which has invalid Database_Type_Code: MICRODATA',
            r'Dataset.csv:6 dropping record',
            r'Dataset.csv:8 DS7 has different observation type AMT from other datasets in database DB_TAB: None',
            r'27 errors were encountered during processing',
        ]

        warnings = [msg for msg in cm.output if msg.startswith('WARNING')]
        self.assertEqual(len(exp_warnings), len(warnings))
        for i, warning in enumerate(warnings):
            self.assertRegex(warning, exp_warnings[i])

        infos = [msg for msg in cm.output if msg.startswith('INFO')]
        self.assertEqual(12, len(infos))
        self.assertRegex(infos[8], r'Build created=1970-01-01T00:00:00 best_effort=True dataset_filter="" geography_file="" versions_data=30 versions_schema=1.4 versions_script=1.4.0')
