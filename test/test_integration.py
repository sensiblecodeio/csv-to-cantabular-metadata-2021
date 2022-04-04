import json
import unittest.mock
import unittest
import pathlib
import os
import ons_csv_to_ctb_json_main

class TestIntegration(unittest.TestCase):
    def test_directory_validity(self):
        """Check that a sensible error is raised if the input/output directory is invalid."""
        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata')
        output_dir = os.path.join(file_dir, 'out')
        invalid_dir = os.path.join(file_dir, 'invalid')

        expected_error = f'{invalid_dir} does not exist or is not a dir'
        with unittest.mock.patch('sys.argv', ['test', '-i', invalid_dir, '-o', output_dir]):
            with self.assertRaisesRegex(ValueError, expected_error):
                ons_csv_to_ctb_json_main.main()

        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', invalid_dir]):
            with self.assertRaisesRegex(ValueError, expected_error):
                ons_csv_to_ctb_json_main.main()

        expected_error = f'{__file__} does not exist or is not a dir'
        with unittest.mock.patch('sys.argv', ['test', '-i', __file__, '-o', output_dir]):
            with self.assertRaisesRegex(ValueError, expected_error):
                ons_csv_to_ctb_json_main.main()

        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', __file__]):
            with self.assertRaisesRegex(ValueError, expected_error):
                ons_csv_to_ctb_json_main.main()

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

            with open(os.path.join(output_dir, 'table-metadata.json')) as f:
                table_metadata = json.load(f)
            with open(os.path.join(file_dir, 'expected/table-metadata.json')) as f:
                expected_table_metadata = json.load(f)
            self.assertEqual(table_metadata, expected_table_metadata)
