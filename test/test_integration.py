import json
import unittest.mock
import unittest
import pathlib
import os
from datetime import datetime
import ons_csv_to_ctb_json_main

FILENAME_TABLES = 'cantabm_v10-2-3_unknown-metadata-version_tables-md_19700101-1.json'
FILENAME_DATASET = 'cantabm_v10-2-3_unknown-metadata-version_dataset-md_19700101-1.json'
FILENAME_SERVICE = 'cantabm_v10-2-3_unknown-metadata-version_service-md_19700101-1.json'

FILENAME_TABLES_NO_GEO = 't_cantabm_v10-2-3_no-geo_tables-md_19700101-2.json'
FILENAME_DATASET_NO_GEO = 't_cantabm_v10-2-3_no-geo_dataset-md_19700101-2.json'
FILENAME_SERVICE_NO_GEO = 't_cantabm_v10-2-3_no-geo_service-md_19700101-2.json'

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

    def test_metadata_master_version(self):
        """Check that a SystemExit is raised if the metadata master version is invalid."""
        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata')
        output_dir = os.path.join(file_dir, 'out')

        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir,
                                              '-m', 'a/../b']):
            with self.assertRaises(SystemExit):
                ons_csv_to_ctb_json_main.main()

    def test_build_number(self):
        """Check that a SystemExit is raised if the build number is invalid."""
        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata')
        output_dir = os.path.join(file_dir, 'out')

        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir,
                                              '-b', 'a']):
            with self.assertRaises(SystemExit):
                ons_csv_to_ctb_json_main.main()

        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir,
                                              '-b', '-1']):
            with self.assertRaises(SystemExit):
                ons_csv_to_ctb_json_main.main()

    def test_clashing_base_dataset_name(self):
        """Check that a sensible error is raised if the base dataset name clashes with another dataset."""
        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata')
        output_dir = os.path.join(file_dir, 'out')

        expected_error = 'Dataset has same case insensitive name as base dataset: DB1'
        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir,
                                              '--base-dataset-name', 'DB1']):
            with self.assertRaisesRegex(ValueError, expected_error):
                ons_csv_to_ctb_json_main.main()

        expected_error = 'Dataset has same case insensitive name as base dataset: db1'
        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir,
                                              '--base-dataset-name', 'db1']):
            with self.assertRaisesRegex(ValueError, expected_error):
                ons_csv_to_ctb_json_main.main()

    def test_invalid_geo_args(self):
        """Check that a sensible error is raised if geography args are invalid."""
        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata')
        output_dir = os.path.join(file_dir, 'out')
        geo_dir = os.path.join(file_dir, 'geography')

        geo1_file = os.path.join(geo_dir, 'geography1.csv')
        expected_error = f"Some geography filenames are specified multiple times: \['{geo1_file}'\]"
        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir,
                                              '-g', geo1_file, '-g', geo1_file]):
            with self.assertRaisesRegex(ValueError, expected_error):
                ons_csv_to_ctb_json_main.main()

        invalid_dir = os.path.join(file_dir, 'invalid')
        expected_error = f'{invalid_dir} does not exist or is not a dir'
        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir,
                                              '-d', invalid_dir]):
            with self.assertRaisesRegex(ValueError, expected_error):
                ons_csv_to_ctb_json_main.main()

        with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir,
                                              '-d', geo_dir, '-g', geo1_file]):
            with self.assertRaises(SystemExit):
                ons_csv_to_ctb_json_main.main()

    @unittest.mock.patch('ons_csv_to_ctb_json_main.datetime')
    def test_generated_json(self, mock_datetime):
        """Generate JSON from source CSV and compare it with expected values."""
        mock_datetime.now.return_value = datetime(1970, 1, 1)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata')
        output_dir = os.path.join(file_dir, 'out')
        geo1_file = os.path.join(input_dir, 'geography/geography1.csv')
        geo2_file = os.path.join(input_dir, 'geography/geography2.csv')
        geo_dir = os.path.join(input_dir, 'geography')
        for args in [['test', '-i', input_dir, '-o', output_dir, '-g', geo1_file, '-g', geo2_file], ['test', '-i', input_dir, '-o', output_dir, '-d', geo_dir]]:
            with self.assertLogs(level='INFO') as cm:
                with unittest.mock.patch('sys.argv', args):
                    ons_csv_to_ctb_json_main.main()
                    with open(os.path.join(output_dir, FILENAME_SERVICE)) as f:
                        service_metadata = json.load(f)
                    with open(os.path.join(file_dir, 'expected/service-metadata.json')) as f:
                        expected_service_metadata = json.load(f)
                    self.assertEqual(service_metadata, expected_service_metadata,
                                     msg=f'Comparing out/{FILENAME_SERVICE} and expected/service-metadata.json')

                    with open(os.path.join(output_dir, FILENAME_DATASET)) as f:
                        dataset_metadata = json.load(f)
                    with open(os.path.join(file_dir, 'expected/dataset-metadata.json')) as f:
                        expected_dataset_metadata = json.load(f)
                    self.assertEqual(dataset_metadata, expected_dataset_metadata,
                                     msg=f'Comparing out/{FILENAME_DATASET} and expected/dataset-metadata.json')

                    with open(os.path.join(output_dir, FILENAME_TABLES)) as f:
                        table_metadata = json.load(f)
                    with open(os.path.join(file_dir, 'expected/table-metadata.json')) as f:
                        expected_table_metadata = json.load(f)
                    self.assertEqual(table_metadata, expected_table_metadata,
                                     f'Comparing out/{FILENAME_TABLES} and expected/table-metadata.json')

            self.assertEqual(17, len(cm.output))
            self.assertRegex(cm.output[4], r"Labels supplied for these geographic classifications: \['GEO1', 'GEO2'\]")
            self.assertRegex(cm.output[13], r'Build created=1970-01-01T00:00:00 best_effort=False dataset_filter="" geography_file="geography1.csv,geography2.csv" versions_data=30 versions_schema=1.4 versions_script=1.4.0$')

    @unittest.mock.patch('ons_csv_to_ctb_json_main.datetime')
    def test_no_geography_file(self, mock_datetime):
        """Generate JSON from source CSV and compare it with expected values."""
        mock_datetime.now.return_value = datetime(1970, 1, 1)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        file_dir = pathlib.Path(__file__).parent.resolve()
        input_dir = os.path.join(file_dir, 'testdata')
        output_dir = os.path.join(file_dir, 'out')
        with self.assertLogs(level='INFO') as cm:
            with unittest.mock.patch('sys.argv', ['test', '-i', input_dir, '-o', output_dir,
                '-m', 'no-geo', '-b', '2', '-p', 't', '--base-dataset-name', 'dummy']):
                ons_csv_to_ctb_json_main.main()
                with open(os.path.join(output_dir, FILENAME_SERVICE_NO_GEO)) as f:
                    service_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/service-metadata-no-geo.json')) as f:
                    expected_service_metadata = json.load(f)
                self.assertEqual(service_metadata, expected_service_metadata,
                                 f'Comparing out/{FILENAME_SERVICE_NO_GEO} and expected/service-metadata-no-geo.json')

                with open(os.path.join(output_dir, FILENAME_DATASET_NO_GEO)) as f:
                    dataset_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/dataset-metadata-no-geo.json')) as f:
                    expected_dataset_metadata = json.load(f)
                self.assertEqual(dataset_metadata, expected_dataset_metadata,
                                 f'Comparing out/{FILENAME_DATASET_NO_GEO} and expected/dataset-metadata-no-geo.json')

                with open(os.path.join(output_dir, FILENAME_TABLES_NO_GEO)) as f:
                    table_metadata = json.load(f)
                with open(os.path.join(file_dir, 'expected/table-metadata.json')) as f:
                    expected_table_metadata = json.load(f)
                self.assertEqual(table_metadata, expected_table_metadata,
                                 f'Comparing out/{FILENAME_TABLES_NO_GEO} and expected/table-metadata.json')

        self.assertEqual(15, len(cm.output))
        self.assertRegex(cm.output[11], r'Build created=1970-01-01T00:00:00 best_effort=False dataset_filter="" geography_file="" versions_data=30 versions_schema=1.4 versions_script=1.4.0$')
