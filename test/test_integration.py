import json
import unittest.mock
import unittest
import pathlib
import os
import ons_csv_to_ctb_json_main

class TestIntegration(unittest.TestCase):
    def test_generated_json(self):
        """Generate JSON from source CSV and compare it with expected values."""
        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata')
        output_dir = os.path.join(file_dir, 'out')
        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir]):
            ons_csv_to_ctb_json_main.main()
            with open(os.path.join(output_dir, 'service-metadata.json')) as f:
                service_metadata = json.load(f)
            with open(os.path.join(file_dir, 'expected/service-metadata.json')) as f:
                expected_service_metadata = json.load(f)
            self.assertEqual(service_metadata, expected_service_metadata)

            with open(os.path.join(output_dir, 'dataset-metadata.json')) as f:
                dataset_metadata = json.load(f)
            with open(os.path.join(file_dir, 'expected/dataset-metadata.json')) as f:
                expected_dataset_metadata = json.load(f)
            self.assertEqual(dataset_metadata, expected_dataset_metadata)
