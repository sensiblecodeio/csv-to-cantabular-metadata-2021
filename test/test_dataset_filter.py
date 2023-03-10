import json
import unittest.mock
import unittest
import pathlib
import os
import logging
from io import StringIO
from datetime import datetime
import ons_csv_to_ctb_json_main

FILENAME_TABLES = 'cantabm_v10-2-2_dataset-filter_tables-md_19700101-1.json'
FILENAME_DATASET = 'cantabm_v10-2-2_dataset-filter_dataset-md_19700101-1.json'
FILENAME_SERVICE = 'cantabm_v10-2-2_dataset-filter_service-md_19700101-1.json'

class TestTopicSummary(unittest.TestCase):
    @unittest.mock.patch('ons_csv_to_ctb_json_main.datetime')
    def test_generated_json_dataset_filter(self, mock_datetime):
        """Generate JSON from source CSV and compare it with expected values."""
        mock_datetime.now.return_value = datetime(1970, 1, 1)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata/dataset_filter')
        output_dir = os.path.join(file_dir, 'out')

        with self.assertLogs(level='INFO') as cm:
            with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir, '-m', 'dataset-filter', '--dataset-filter', 'TS,"BLAH"']):
                ons_csv_to_ctb_json_main.main()
                with open(os.path.join(output_dir, FILENAME_SERVICE)) as f:
                    service_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/service-metadata-dataset-filter.json')) as f:
                    expected_service_metadata = json.load(f)
                self.assertEqual(service_metadata, expected_service_metadata,
                                 msg=f'Comparing out/{FILENAME_SERVICE} and expected/service-metadata-dataset-filter.json')

                with open(os.path.join(output_dir, FILENAME_DATASET)) as f:
                    dataset_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/dataset-metadata-dataset-filter.json')) as f:
                    expected_dataset_metadata = json.load(f)
                self.assertEqual(dataset_metadata, expected_dataset_metadata,
                                 msg=f'Comparing out/{FILENAME_DATASET} and expected/dataset-metadata-dataset-filter.json')

                with open(os.path.join(output_dir, FILENAME_TABLES)) as f:
                    table_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/table-metadata-dataset-filter.json')) as f:
                    expected_table_metadata = json.load(f)
                self.assertEqual(table_metadata, expected_table_metadata,
                                 msg=f'Comparing out/{FILENAME_TABLES} and expected/table-metadata-dataset-filter.json')

        self.assertEqual(15, len(cm.output))
        self.assertRegex(cm.output[2], r'Dataset filter: TS,"BLAH"')
        self.assertRegex(cm.output[6], r"Dataset.csv dropped 1 records related to datasets with Dataset_Mnemonics that do not start with one of: \['TS', '\"BLAH\"']")
        self.assertRegex(cm.output[7], r"Dataset_Variable.csv dropped 1 records related to datasets with Dataset_Mnemonics that do not start with one of: \['TS', '\"BLAH\"']")
        self.assertRegex(cm.output[11], r'Build created=1970-01-01T00:00:00 best_effort=False dataset_filter="TS,\\"BLAH\\"" geography_file="" versions_data=30 versions_schema=1.4 versions_script=1.4.0')

    @unittest.mock.patch('ons_csv_to_ctb_json_main.datetime')
    def test_errors_in_unfiltered_datasets(self, mock_datetime):
        """Ensure that errors are seen when --dataset-filter flag not set."""
        mock_datetime.now.return_value = datetime(1970, 1, 1)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata/dataset_filter')
        output_dir = os.path.join(file_dir, 'out')

        with self.assertLogs(level='WARNING') as cm:
            with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir, '-m', 'dataset-filter-issues', '--best-effort']):
                ons_csv_to_ctb_json_main.main()

        warnings = [
            r'Dataset_Variable.csv:2 Lowest_Geog_Variable_Flag set on non-geographic variable VAR1 for dataset DS1',
            r'Dataset.csv:3 DS1 has different observation type PCT from other datasets in database DB1: AMT',
            r'2 errors were encountered during processing',
        ]

        self.assertEqual(len(warnings), len(cm.output))
        for i, warning in enumerate(cm.output):
            self.assertRegex(warning, warnings[i])
