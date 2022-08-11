import json
import unittest.mock
import unittest
import pathlib
import os
import logging
from io import StringIO
from datetime import date
import ons_csv_to_ctb_json_main

FILENAME_TABLES = 'cantabm_v10-1-0_topic-summary_tables-md_19700101-1.json'
FILENAME_DATASET = 'cantabm_v10-1-0_topic-summary_dataset-md_19700101-1.json'
FILENAME_SERVICE = 'cantabm_v10-1-0_topic-summary_service-md_19700101-1.json'

class TestTopicSummary(unittest.TestCase):
    @unittest.mock.patch('ons_csv_to_ctb_json_main.date')
    def test_generated_json_topic_summary(self, mock_date):
        """Generate JSON from source CSV and compare it with expected values."""
        mock_date.today.return_value = date(1970, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata/topic_summary')
        output_dir = os.path.join(file_dir, 'out')

        with self.assertLogs(level='INFO') as cm:
            with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir, '-m', 'topic-summary', '--topic-summary']):
                ons_csv_to_ctb_json_main.main()
                with open(os.path.join(output_dir, FILENAME_SERVICE)) as f:
                    service_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/service-metadata.json')) as f:
                    expected_service_metadata = json.load(f)
                self.assertEqual(service_metadata, expected_service_metadata,
                                 msg=f'Comparing out/{FILENAME_SERVICE} and expected/service-metadata.json')

                with open(os.path.join(output_dir, FILENAME_DATASET)) as f:
                    dataset_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/dataset-metadata-topic-summary.json')) as f:
                    expected_dataset_metadata = json.load(f)
                self.assertEqual(dataset_metadata, expected_dataset_metadata,
                                 msg=f'Comparing out/{FILENAME_DATASET} and expected/dataset-metadata-topic-summary.json')

                with open(os.path.join(output_dir, FILENAME_TABLES)) as f:
                    table_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/table-metadata-topic-summary.json')) as f:
                    expected_table_metadata = json.load(f)
                self.assertEqual(table_metadata, expected_table_metadata,
                                 msg=f'Comparing out/{FILENAME_TABLES} and expected/table-metadata-topic-summary.json')

        self.assertEqual(13, len(cm.output))
        self.assertRegex(cm.output[5], r'Dataset.csv dropped 1 records related to non Topic Summary datasets')
        self.assertRegex(cm.output[6], r'Dataset_Variable.csv dropped 1 records related to non Topic Summary datasets')

    @unittest.mock.patch('ons_csv_to_ctb_json_main.date')
    def test_errors_in_non_topic_summary_datasets(self, mock_date):
        """Ensure that errors are seen when --topic-summary flag not set."""
        mock_date.today.return_value = date(1970, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata/topic_summary')
        output_dir = os.path.join(file_dir, 'out')

        with self.assertLogs(level='WARNING') as cm:
            with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir, '-m', 'topic-summary-issues', '--best-effort']):
                ons_csv_to_ctb_json_main.main()

        warnings = [
            r'Dataset_Variable.csv:2 Lowest_Geog_Variable_Flag set on non-geographic variable VAR1 for dataset DS1',
            r'Dataset.csv:3 DS1 has different observation type PCT from other datasets in database DB1: AMT',
            r'2 errors were encountered during processing',
        ]

        self.assertEqual(len(warnings), len(cm.output))
        for i, warning in enumerate(cm.output):
            self.assertRegex(warning, warnings[i])
