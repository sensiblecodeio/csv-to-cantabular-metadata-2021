Introduction
============

`bin/ons_csv_to_ctb_json_main.py` is an application that loads source metadata files in CSV format
and converts them to hierarchical JSON that can be loaded into `cantabular-metadata`.

It is compatible with version `1.1` of the metadata schema and version `9.3.0` of `cantabular-metadata`.

This is version `1.1.alpha` of the CSV to JSON processing software and is subject to change.

The applications only use packages in the Python standard library.

Converting CSV to JSON
======================

Most of the source metadata are contained in a set of CSV files based on the metadata schema.
However, category codes, names and Welsh names for geographic variables are supplied in a separate
lookup file. The main CSV file set must not contain categories for geographic variables.

Using test data
---------------

The `test/testdata` directory contains some sample CSV files that are used as part of continuous
integration testing. They contain dummy data that are intended to exercise the capabilities of the
software. Category information for geographic variables is supplied in `test/testdata/geography/geography.csv`.
The data can be used to verify the operation of `ons_csv_to_ctb_json_main.py`.

To convert the source CSV files to JSON files in `ctb_metadata_files/` run:
```
python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -g test/testdata/geography/geography.csv -o ctb_metadata_files/
```

Basic logging will be displayed by default, including the number of high-level Cantabular metadata
objects loaded and the name of the output files.
```
> python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -g test/testdata/geography/geography.csv -o ctb_metadata_files/
t=2022-05-09 21:26:50,348 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.alpha
t=2022-05-09 21:26:50,348 lvl=INFO msg=CSV source directory: test/testdata/
t=2022-05-09 21:26:50,348 lvl=INFO msg=Geography file: test/testdata/geography/geography.csv
t=2022-05-09 21:26:50,350 lvl=INFO msg=Reading test/testdata/geography/geography.csv: found Welsh labels for unknown classification: OTHER
t=2022-05-09 21:26:50,350 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-05-09 21:26:50,350 lvl=INFO msg=Dropped non public classification: GEO_PRIV
t=2022-05-09 21:26:50,350 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-05-09 21:26:50,351 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-05-09 21:26:50,351 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-05-09 21:26:50,351 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-05-09 21:26:50,351 lvl=INFO msg=Loaded service metadata
t=2022-05-09 21:26:50,351 lvl=INFO msg=Output files will be written in Cantabular 9.3.0 format
t=2022-05-09 21:26:50,352 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/cantabm_v9-3-0_unknown-metadata-version_dataset-md_20220509-1.json
t=2022-05-09 21:26:50,353 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/cantabm_v9-3-0_unknown-metadata-version_tables-md_20220509-1.json
t=2022-05-09 21:26:50,353 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/cantabm_v9-3-0_unknown-metadata-version_service-md_20220509-1.json
```

More detailed information can be obtained by running with a `-l DEBUG` flag e.g.:
```
> python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -g test/testdata/geography/geography.csv -o ctb_metadata_files/ -l DEBUG
t=2022-05-09 21:27:20,066 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.alpha
t=2022-05-09 21:27:20,066 lvl=INFO msg=CSV source directory: test/testdata/
t=2022-05-09 21:27:20,066 lvl=INFO msg=Geography file: test/testdata/geography/geography.csv
t=2022-05-09 21:27:20,067 lvl=DEBUG msg=Creating classification for geographic variable: GEO1
t=2022-05-09 21:27:20,067 lvl=DEBUG msg=Creating classification for geographic variable: GEO2
t=2022-05-09 21:27:20,067 lvl=DEBUG msg=Creating classification for geographic variable: GEO_PRIV
t=2022-05-09 21:27:20,067 lvl=INFO msg=Reading test/testdata/geography/geography.csv: found Welsh labels for unknown classification: OTHER
t=2022-05-09 21:27:20,068 lvl=DEBUG msg=Loaded metadata for Cantabular variable: CLASS1
t=2022-05-09 21:27:20,068 lvl=DEBUG msg=Loaded metadata for Cantabular variable: CLASS2
t=2022-05-09 21:27:20,068 lvl=DEBUG msg=Loaded metadata for Cantabular variable: CLASS3
t=2022-05-09 21:27:20,068 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-05-09 21:27:20,068 lvl=DEBUG msg=Loaded metadata for Cantabular variable: GEO1
t=2022-05-09 21:27:20,068 lvl=DEBUG msg=Loaded metadata for Cantabular variable: GEO2
t=2022-05-09 21:27:20,068 lvl=INFO msg=Dropped non public classification: GEO_PRIV
t=2022-05-09 21:27:20,068 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-05-09 21:27:20,068 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: DB1
t=2022-05-09 21:27:20,068 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: DB2
t=2022-05-09 21:27:20,068 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: DB3
t=2022-05-09 21:27:20,068 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-05-09 21:27:20,069 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS1
t=2022-05-09 21:27:20,069 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS2
t=2022-05-09 21:27:20,069 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS3
t=2022-05-09 21:27:20,069 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-05-09 21:27:20,069 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS4
t=2022-05-09 21:27:20,069 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-05-09 21:27:20,069 lvl=INFO msg=Loaded service metadata
t=2022-05-09 21:27:20,069 lvl=INFO msg=Output files will be written in Cantabular 9.3.0 format
t=2022-05-09 21:27:20,070 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/cantabm_v9-3-0_unknown-metadata-version_dataset-md_20220509-1.json
t=2022-05-09 21:27:20,071 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/cantabm_v9-3-0_unknown-metadata-version_tables-md_20220509-1.json
t=2022-05-09 21:27:20,071 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/cantabm_v9-3-0_unknown-metadata-version_service-md_20220509-1.json
```

Output file names
-----------------

The output file names are formatted as follows:
```
<prefix>cantabm_9-3-0_<metadata master version>_dataset-md_<date as yyyymmdd-><build number>.json
<prefix>cantabm_9-3-0_<metadata master version>_service-md_<date as yyyymmdd-><build number>.json
<prefix>cantabm_9-3-0_<metadata master version>_tables-md_<date as yyyymmdd-><build number>.json
```

The `prefix`, `metadata master version` and `build number` can be specified using command line
arguments as described in the help text for `ons_csv_to_ctb_json_main.py`:
```
  -p {d,t,tu}, --file_prefix {d,t,tu}
                        Prefix to use in output filenames: d=dev, t=test,
                        tu=tuning (default: no prefix i.e. operational)
  -m METADATA_MASTER_VERSION, --metadata_master_version METADATA_MASTER_VERSION
                        Metadata master version to use in output filenames
                        (default: unknown-metadata-version)
  -b BUILD_NUMBER, --build_number BUILD_NUMBER
                        Build number to use in output filenames (default: 1)

```

For example:
```
> python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -g test/testdata/geography/geography.csv -o ctb_metadata_files/ -p t -m test -b 42
t=2022-05-09 21:27:57,633 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.alpha
t=2022-05-09 21:27:57,633 lvl=INFO msg=CSV source directory: test/testdata/
t=2022-05-09 21:27:57,633 lvl=INFO msg=Geography file: test/testdata/geography/geography.csv
t=2022-05-09 21:27:57,634 lvl=INFO msg=Reading test/testdata/geography/geography.csv: found Welsh labels for unknown classification: OTHER
t=2022-05-09 21:27:57,635 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-05-09 21:27:57,635 lvl=INFO msg=Dropped non public classification: GEO_PRIV
t=2022-05-09 21:27:57,635 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-05-09 21:27:57,635 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-05-09 21:27:57,636 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-05-09 21:27:57,636 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-05-09 21:27:57,636 lvl=INFO msg=Loaded service metadata
t=2022-05-09 21:27:57,636 lvl=INFO msg=Output files will be written in Cantabular 9.3.0 format
t=2022-05-09 21:27:57,637 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/t_cantabm_v9-3-0_test_dataset-md_20220509-42.json
t=2022-05-09 21:27:57,637 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/t_cantabm_v9-3-0_test_tables-md_20220509-42.json
t=2022-05-09 21:27:57,638 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/t_cantabm_v9-3-0_test_service-md_20220509-42.json
```

Using externally sourced files
------------------------------

To convert the externally sourced metadata CSV files currently being used for testing, first fixup the source files:
```
python3 bin/fixup.py -i <SOURCE_DIRECTORY> --g <GEOGRAPHY_FILENAME> -o modified/
```

The geography file will be placed in the `modified/` directory and will have the same base name as the original file.

This will load the sample files and modify them slightly so that they can be processed by `ons_csv_to_ctb_json_main.py`.
This step will not be needed for production.

Then convert the files to JSON:
```
python3 bin/ons_csv_to_ctb_json_main.py -i modified/ -g modified/<GEOGRAPHY_FILENAME> -o ctb_metadata_files/
```

Using 2011 census teaching file metadata
----------------------------------------

The ONS produced a 1% sample microdata teaching file based on 2011 census data. It can be accessed here:

https://www.ons.gov.uk/census/2011census/2011censusdata/censusmicrodata/microdatateachingfile

We have generated some sample metadata for this dataset using publicly available sources. The CSV source files
can be found in the `sample_2011` directory.

Use this command to convert the files to JSON (with debugging enabled):
```
> python3 bin/ons_csv_to_ctb_json_main.py -i sample_2011/ -g sample_2011/geography.csv -o ctb_metadata_files/ -m 2001-sample -l DEBUG
t=2022-05-09 21:28:29,336 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.alpha
t=2022-05-09 21:28:29,336 lvl=INFO msg=CSV source directory: sample_2011/
t=2022-05-09 21:28:29,336 lvl=INFO msg=Geography file: sample_2011/geography.csv
t=2022-05-09 21:28:29,354 lvl=DEBUG msg=Creating classification for geographic variable: Region
t=2022-05-09 21:28:29,354 lvl=DEBUG msg=Creating classification for geographic variable: Country
t=2022-05-09 21:28:29,356 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Residence Type
t=2022-05-09 21:28:29,356 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Family Composition
t=2022-05-09 21:28:29,356 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Population Base
t=2022-05-09 21:28:29,356 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Sex
t=2022-05-09 21:28:29,356 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Age
t=2022-05-09 21:28:29,356 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Marital Status
t=2022-05-09 21:28:29,356 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Student
t=2022-05-09 21:28:29,356 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Country of Birth
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Health
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Ethnic Group
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Religion
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Economic Activity
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Occupation
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Industry
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Hours worked per week
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Approximated Social Grade
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Region
t=2022-05-09 21:28:29,357 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Country
t=2022-05-09 21:28:29,357 lvl=INFO msg=Loaded metadata for 18 Cantabular variables
t=2022-05-09 21:28:29,358 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: Teaching-Dataset
t=2022-05-09 21:28:29,358 lvl=INFO msg=Loaded metadata for 1 Cantabular datasets
t=2022-05-09 21:28:29,360 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC2101EW
t=2022-05-09 21:28:29,360 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC1117EW
t=2022-05-09 21:28:29,360 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC2107EW
t=2022-05-09 21:28:29,360 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC6107EW
t=2022-05-09 21:28:29,360 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC6112EW
t=2022-05-09 21:28:29,360 lvl=INFO msg=Loaded metadata for 5 Cantabular tables
t=2022-05-09 21:28:29,361 lvl=INFO msg=Loaded service metadata
t=2022-05-09 21:28:29,361 lvl=INFO msg=Output files will be written in Cantabular 9.3.0 format
t=2022-05-09 21:28:29,364 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/cantabm_v9-3-0_2001-sample_dataset-md_20220509-1.json
t=2022-05-09 21:28:29,365 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/cantabm_v9-3-0_2001-sample_tables-md_20220509-1.json
t=2022-05-09 21:28:29,365 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/cantabm_v9-3-0_2001-sample_service-md_20220509-1.json
```

Load the JSON files with cantabular-metadata
============================================

To load the generated JSON files into `cantabular-metadata` (version 9.3.0) run the following
commands, substituting the file names and paths as appropriate:
```
cd ctb_metadata_files
CANTABULAR_METADATA_GRAPHQL_TYPES_FILE=metadata.graphql CANTABULAR_METADATA_SERVICE_FILE=cantabm_v9-3-0_unknown-metadata-version_service-md_20220428-1.json CANTABULAR_METADATA_DATASET_FILES=cantabm_v9-3-0_unknown-metadata-version_dataset-md_20220428-1.json CANTABULAR_METADATA_TABLE_FILES=cantabm_v9-3-0_unknown-metadata-version_tables-md_20220428-1.json <PATH_TO_BINARY>/cantabular-metadata
```

The metadata can be queried via a GraphQL interface. By default this is accessible at:

http://localhost:8493/graphql

`cantabular-metadata` is packaged with the [GraphiQL](https://github.com/graphql/graphiql) IDE
and this can be used to construct GraphQL queries when the service is accessed via a web browser.

The following query can be used to obtain Welsh information for a single named variable (from the test data):

http://localhost:8493/graphql?query=%7Bdataset(name%3A%22DB1%22%2Clang%3A%22cy%22)%7Bvars(names%3A%5B%22CLASS1%22%5D)%7BcatLabels%20name%20label%20all%7D%7D%7D%0A

This query can be used to obtain information for a single named table:

http://localhost:8493/graphql?query=%7Bservice%7Btables(names%3A%20%5B%22DS1%22%5D)%7Bname%20datasetName%20vars%20description%20label%20all%7D%7D%7D%0A

Tests
=====

This repository has tests written using the `unittest` framework. They are run as part of
Continuous Integration testing in the GitHub repository. They can be run manually by running this
command from the base directory:

```
PYTHONPATH=test:bin python3 -m unittest -v
```

Other Cantabular versions
=========================

The `-v` argument can be used to generate output files that are compatible with a different version of Cantabular.
At present only 9.2.0 and 9.3.0 are supported. If any other version is specified then the specified version
will be reflected in the output filenames, but `9.3.0` format will be used.

To generate version 9.2.0 compatible files from the test data use the following command:
```
> python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -g test/testdata/geography/geography.csv -o ctb_metadata_files/ -v 9.2.0
t=2022-05-09 21:40:49,218 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.alpha
t=2022-05-09 21:40:49,218 lvl=INFO msg=CSV source directory: test/testdata/
t=2022-05-09 21:40:49,218 lvl=INFO msg=Geography file: test/testdata/geography/geography.csv
t=2022-05-09 21:40:49,220 lvl=INFO msg=Reading test/testdata/geography/geography.csv: found Welsh labels for unknown classification: OTHER
t=2022-05-09 21:40:49,220 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-05-09 21:40:49,220 lvl=INFO msg=Dropped non public classification: GEO_PRIV
t=2022-05-09 21:40:49,220 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-05-09 21:40:49,221 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-05-09 21:40:49,222 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-05-09 21:40:49,222 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-05-09 21:40:49,222 lvl=INFO msg=Loaded service metadata
t=2022-05-09 21:40:49,222 lvl=INFO msg=Output files will be written in Cantabular 9.2.0 format
t=2022-05-09 21:40:49,223 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/cantabm_v9-2-0_unknown-metadata-version_dataset-md_20220509-1.json
t=2022-05-09 21:40:49,223 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/cantabm_v9-2-0_unknown-metadata-version_service-md_20220509-1.json
```

No tables metadata file is produced. The tables data is embedded in the service metadata file.

To load the files into `cantabular-metadata` version 9.2.0 you need a different GraphQL types
file which can be found `ctb_metadata_files/metadata_9_2_0.graphql`. The files are also specified at
the command line instead of via environment variables.


To load the generated JSON files into `cantabular-metadata` (version 9.2.0) run the following
commands, substituting the file names and paths as appropriate:
```
cd ctb_metadata_files
<PATH_TO_9.2.0_BINARY>/cantabular-metadata metadata_9_2_0.graphql cantabm_v9-2-0_unknown-metadata-version_service-md_20220509-1.json cantabm_v9-2-0_unknown-metadata-version_dataset-md_20220509-1.json
```
