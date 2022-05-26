Introduction
============

`bin/ons_csv_to_ctb_json_main.py` is an application that loads source metadata files in CSV format
and converts them to hierarchical JSON that can be loaded into `cantabular-metadata`.

It is compatible with version `1.1` of the metadata schema and versions `10.0.0`/`9.3.0`/`9.2.0` of
`cantabular-metadata`. `10.0.0` format is used by default and is identical to the `9.3.0` format.

This is version `1.1.delta` of the CSV to JSON processing software and is subject to change.

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
t=2022-05-24 16:40:14,151 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.delta
t=2022-05-24 16:40:14,151 lvl=INFO msg=CSV source directory: test/testdata/
t=2022-05-24 16:40:14,151 lvl=INFO msg=Geography file: test/testdata/geography/geography.csv
t=2022-05-24 16:40:14,153 lvl=INFO msg=Reading test/testdata/geography/geography.csv: found Welsh labels for unknown classification: OTHER
t=2022-05-24 16:40:14,153 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-05-24 16:40:14,153 lvl=INFO msg=Dropped non public classification: GEO_PRIV
t=2022-05-24 16:40:14,153 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-05-24 16:40:14,153 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-05-24 16:40:14,154 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-05-24 16:40:14,154 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-05-24 16:40:14,154 lvl=INFO msg=Loaded service metadata
t=2022-05-24 16:40:14,154 lvl=INFO msg=Output files will be written in Cantabular 10.0.0 format
t=2022-05-24 16:40:14,156 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/cantabm_v10-0-0_unknown-metadata-version_dataset-md_20220524-1.json
t=2022-05-24 16:40:14,156 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/cantabm_v10-0-0_unknown-metadata-version_tables-md_20220524-1.json
t=2022-05-24 16:40:14,156 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/cantabm_v10-0-0_unknown-metadata-version_service-md_20220524-1.json
```

More detailed information can be obtained by running with a `-l DEBUG` flag e.g.:
```
> python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -g test/testdata/geography/geography.csv -o ctb_metadata_files/ -l DEBUG
t=2022-05-24 16:40:46,032 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.delta
t=2022-05-24 16:40:46,033 lvl=INFO msg=CSV source directory: test/testdata/
t=2022-05-24 16:40:46,033 lvl=INFO msg=Geography file: test/testdata/geography/geography.csv
t=2022-05-24 16:40:46,034 lvl=DEBUG msg=Creating classification for geographic variable: GEO1
t=2022-05-24 16:40:46,034 lvl=DEBUG msg=Creating classification for geographic variable: GEO2
t=2022-05-24 16:40:46,034 lvl=DEBUG msg=Creating classification for geographic variable: GEO_PRIV
t=2022-05-24 16:40:46,034 lvl=INFO msg=Reading test/testdata/geography/geography.csv: found Welsh labels for unknown classification: OTHER
t=2022-05-24 16:40:46,035 lvl=DEBUG msg=Loaded metadata for Cantabular variable: CLASS1
t=2022-05-24 16:40:46,035 lvl=DEBUG msg=Loaded metadata for Cantabular variable: CLASS2
t=2022-05-24 16:40:46,035 lvl=DEBUG msg=Loaded metadata for Cantabular variable: CLASS3
t=2022-05-24 16:40:46,035 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-05-24 16:40:46,035 lvl=DEBUG msg=Loaded metadata for Cantabular variable: GEO1
t=2022-05-24 16:40:46,035 lvl=DEBUG msg=Loaded metadata for Cantabular variable: GEO2
t=2022-05-24 16:40:46,035 lvl=INFO msg=Dropped non public classification: GEO_PRIV
t=2022-05-24 16:40:46,035 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-05-24 16:40:46,035 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: DB1
t=2022-05-24 16:40:46,035 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: DB2
t=2022-05-24 16:40:46,035 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: DB3
t=2022-05-24 16:40:46,035 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-05-24 16:40:46,036 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS1
t=2022-05-24 16:40:46,036 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS2
t=2022-05-24 16:40:46,036 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS3
t=2022-05-24 16:40:46,036 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-05-24 16:40:46,036 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS4
t=2022-05-24 16:40:46,036 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-05-24 16:40:46,036 lvl=INFO msg=Loaded service metadata
t=2022-05-24 16:40:46,036 lvl=INFO msg=Output files will be written in Cantabular 10.0.0 format
t=2022-05-24 16:40:46,037 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/cantabm_v10-0-0_unknown-metadata-version_dataset-md_20220524-1.json
t=2022-05-24 16:40:46,038 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/cantabm_v10-0-0_unknown-metadata-version_tables-md_20220524-1.json
t=2022-05-24 16:40:46,038 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/cantabm_v10-0-0_unknown-metadata-version_service-md_20220524-1.json
```

Output file names
-----------------

The output file names are formatted as follows:
```
<prefix>cantabm_10-0-0_<metadata master version>_dataset-md_<date as yyyymmdd-><build number>.json
<prefix>cantabm_10-0-0_<metadata master version>_service-md_<date as yyyymmdd-><build number>.json
<prefix>cantabm_10-0-0_<metadata master version>_tables-md_<date as yyyymmdd-><build number>.json
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
t=2022-05-24 16:41:24,500 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.delta
t=2022-05-24 16:41:24,500 lvl=INFO msg=CSV source directory: test/testdata/
t=2022-05-24 16:41:24,500 lvl=INFO msg=Geography file: test/testdata/geography/geography.csv
t=2022-05-24 16:41:24,502 lvl=INFO msg=Reading test/testdata/geography/geography.csv: found Welsh labels for unknown classification: OTHER
t=2022-05-24 16:41:24,502 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-05-24 16:41:24,502 lvl=INFO msg=Dropped non public classification: GEO_PRIV
t=2022-05-24 16:41:24,502 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-05-24 16:41:24,502 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-05-24 16:41:24,503 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-05-24 16:41:24,503 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-05-24 16:41:24,503 lvl=INFO msg=Loaded service metadata
t=2022-05-24 16:41:24,503 lvl=INFO msg=Output files will be written in Cantabular 10.0.0 format
t=2022-05-24 16:41:24,504 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/t_cantabm_v10-0-0_test_dataset-md_20220524-42.json
t=2022-05-24 16:41:24,505 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/t_cantabm_v10-0-0_test_tables-md_20220524-42.json
t=2022-05-24 16:41:24,505 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/t_cantabm_v10-0-0_test_service-md_20220524-42.json
```

Using data with errors
----------------------

`ons_csv_to_ctb_json_main.py` fails on the first error. This is intentional as the data must be
correct for use in production. For debug purposes a `--best-effort` flag can be used to continue
processing when errors are found and to make a **best effort** to generate output. Typically this
will result in some data loss as some records will be dropped and some fields will be ignored.

This repository contains some test data that is full of errors. It can be used to demonstrate the usage
of the `--best-effort` flag as shown below:
```
> python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/best_effort  -o ctb_metadata_files/ -m best-effort --best-effort
t=2022-05-24 20:29:16,314 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.delta
t=2022-05-24 20:29:16,314 lvl=INFO msg=CSV source directory: test/testdata/best_effort
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Classification.csv:3 no value supplied for required field Variable_Mnemonic
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Classification.csv:3 dropping record
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Classification.csv:4 duplicate value CLASS1 for Classification_Mnemonic
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Classification.csv:4 dropping record
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Classification.csv:5 invalid value x for Number_Of_Category_Items
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Classification.csv:5 ignoring field Number_Of_Category_Items
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Category_Mapping.csv:3 different Codebook_Mnemonic values specified for classification CLASS1: CLASS1 (Codebook A) and CLASS1 (Codebook)
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Category_Mapping.csv:4 CLASS1 (Codebook) is Codebook_Mnemonic for both CLASS1 and CLASS3
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Category_Mapping.csv:4 ignoring field Codebook_Mnemonic
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Category_Mapping.csv:5 CLASS1 is an invalid Codebook_Mnemonic for classification CLASS4 as it is already the Classification_Mnemonic for another classification
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Category_Mapping.csv:5 ignoring field Codebook_Mnemonic
t=2022-05-24 20:29:16,316 lvl=WARNING msg=Reading test/testdata/best_effort/Category.csv Unexpected number of categories for CLASS1: expected 4 but found 1
t=2022-05-24 20:29:16,316 lvl=INFO msg=No geography file specified
t=2022-05-24 20:29:16,316 lvl=INFO msg=Loaded metadata for 6 Cantabular variables
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Database_Variable.csv Lowest_Geog_Variable_Flag set on GEO3 and GEO1 for database DB1
t=2022-05-24 20:29:16,317 lvl=INFO msg=Loaded metadata for 1 Cantabular datasets
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:4 duplicate value combo DS1/VAR1 for Dataset_Mnemonic/Variable_Mnemonic
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:4 dropping record
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:2 Lowest_Geog_Variable_Flag set on non-geographic variable VAR1 for dataset DS1
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:2 Processing_Priority not specified for classification CLASS1 in dataset DS1
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:2 using 0 for Processing_Priority
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:3 Classification_Mnemonic must not be specified for geographic variable GEO1 in dataset DS1
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:3 Processing_Priority must not be specified for geographic variable GEO1 in dataset DS1
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:5 Lowest_Geog_Variable_Flag set on variable GEO2 and GEO1 for dataset DS1
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:7 Classification must be specified for non-geographic VAR2 in dataset DS1
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:7 dropping record
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:8 Invalid classification CLASS1 specified for variable VAR3 in dataset DS1
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv:8 dropping record
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset_Variable.csv Invalid processing_priorities [0] for dataset DS1
t=2022-05-24 20:29:16,317 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset.csv:3 DS2 has classification CLASS3 that is not in database DB1
t=2022-05-24 20:29:16,318 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset.csv:4 DS3 has no associated classifications or geographic variable
t=2022-05-24 20:29:16,318 lvl=WARNING msg=Reading test/testdata/best_effort/Dataset.csv:4 dropping record
t=2022-05-24 20:29:16,318 lvl=INFO msg=Loaded metadata for 2 Cantabular tables
t=2022-05-24 20:29:16,318 lvl=INFO msg=Loaded service metadata
t=2022-05-24 20:29:16,318 lvl=WARNING msg=19 errors were encountered during processing
t=2022-05-24 20:29:16,318 lvl=INFO msg=Output files will be written in Cantabular 10.0.0 format
t=2022-05-24 20:29:16,318 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/cantabm_v10-0-0_best-effort_dataset-md_20220524-1.json
t=2022-05-24 20:29:16,319 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/cantabm_v10-0-0_best-effort_tables-md_20220524-1.json
t=2022-05-24 20:29:16,319 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/cantabm_v10-0-0_best-effort_service-md_20220524-1.json
```

Many lines contain strings such as `test/testdata/best_effort/Dataset.csv:4` this means that an error has been detected
on row 4 of the `Dataset.csv` file. The header will be row 1.

The `--best-effort` flag is for debug purposes only.

Using 2011 census teaching file metadata
----------------------------------------

The ONS produced a 1% sample microdata teaching file based on 2011 census data. It can be accessed here:

https://www.ons.gov.uk/census/2011census/2011censusdata/censusmicrodata/microdatateachingfile

We have generated some sample metadata for this dataset using publicly available sources. The CSV source files
can be found in the `sample_2011` directory.

Use this command to convert the files to JSON (with debugging enabled):
```
> python3 bin/ons_csv_to_ctb_json_main.py -i sample_2011/ -g sample_2011/geography.csv -o ctb_metadata_files/ -m 2001-sample -l DEBUG
t=2022-05-24 16:51:22,438 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.delta
t=2022-05-24 16:51:22,438 lvl=INFO msg=CSV source directory: sample_2011/
t=2022-05-24 16:51:22,438 lvl=INFO msg=Geography file: sample_2011/geography.csv
t=2022-05-24 16:51:22,441 lvl=DEBUG msg=Creating classification for geographic variable: Region
t=2022-05-24 16:51:22,442 lvl=DEBUG msg=Creating classification for geographic variable: Country
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Residence Type
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Family Composition
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Population Base
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Sex
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Age
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Marital Status
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Student
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Country of Birth
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Health
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Ethnic Group
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Religion
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Economic Activity
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Occupation
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Industry
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Hours worked per week
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Approximated Social Grade
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Region
t=2022-05-24 16:51:22,443 lvl=DEBUG msg=Loaded metadata for Cantabular variable: Country
t=2022-05-24 16:51:22,443 lvl=INFO msg=Loaded metadata for 18 Cantabular variables
t=2022-05-24 16:51:22,444 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: Teaching-Dataset
t=2022-05-24 16:51:22,444 lvl=INFO msg=Loaded metadata for 1 Cantabular datasets
t=2022-05-24 16:51:22,445 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC2101EW
t=2022-05-24 16:51:22,445 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC1117EW
t=2022-05-24 16:51:22,445 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC2107EW
t=2022-05-24 16:51:22,445 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC6107EW
t=2022-05-24 16:51:22,445 lvl=DEBUG msg=Loaded metadata for Cantabular table: LC6112EW
t=2022-05-24 16:51:22,445 lvl=INFO msg=Loaded metadata for 5 Cantabular tables
t=2022-05-24 16:51:22,445 lvl=INFO msg=Loaded service metadata
t=2022-05-24 16:51:22,445 lvl=INFO msg=Output files will be written in Cantabular 10.0.0 format
t=2022-05-24 16:51:22,448 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/cantabm_v10-0-0_2001-sample_dataset-md_20220524-1.json
t=2022-05-24 16:51:22,449 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/cantabm_v10-0-0_2001-sample_tables-md_20220524-1.json
t=2022-05-24 16:51:22,449 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/cantabm_v10-0-0_2001-sample_service-md_20220524-1.json
```

Load the JSON files with cantabular-metadata
============================================

To load the generated JSON files into `cantabular-metadata` (version 10.0.0) run the following
commands, substituting the file names and paths as appropriate:
```
cd ctb_metadata_files
CANTABULAR_METADATA_GRAPHQL_TYPES_FILE=metadata.graphql CANTABULAR_METADATA_SERVICE_FILE=cantabm_v10-0-0_unknown-metadata-version_service-md_20220524-1.json CANTABULAR_METADATA_DATASET_FILES=cantabm_v10-0-0_unknown-metadata-version_dataset-md_20220524-1.json CANTABULAR_METADATA_TABLE_FILES=cantabm_v10-0-0_unknown-metadata-version_tables-md_20220524-1.json <PATH_TO_BINARY>/cantabular-metadata
```

The metadata can be queried via a GraphQL interface. By default this is accessible at:

http://localhost:8493/graphql

`cantabular-metadata` is packaged with the [GraphiQL](https://github.com/graphql/graphiql) IDE
and this can be used to construct GraphQL queries when the service is accessed via a web browser.

The following query can be used to obtain Welsh information for a single named variable (from the test data):

http://localhost:8493/graphql?query=%7Bdataset(name%3A%22DB1%22%2Clang%3A%22cy%22)%7Bvars(names%3A%5B%22CLASS1%20(Codebook)%22%5D)%7BcatLabels%20name%20label%20all%7D%7D%7D%0A

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
At present only 9.2.0, 9.3.0 and 10.0.0 are supported. If any other version is specified then the specified version
will be reflected in the output filenames, but `10.0.0` format will be used.

To generate version 9.2.0 compatible files from the test data use the following command:
```
> python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -g test/testdata/geography/geography.csv -o ctb_metadata_files/ -v 9.2.0
t=2022-05-24 16:52:04,154 lvl=INFO msg=ons_csv_to_ctb_json_main.py version 1.1.delta
t=2022-05-24 16:52:04,154 lvl=INFO msg=CSV source directory: test/testdata/
t=2022-05-24 16:52:04,154 lvl=INFO msg=Geography file: test/testdata/geography/geography.csv
t=2022-05-24 16:52:04,156 lvl=INFO msg=Reading test/testdata/geography/geography.csv: found Welsh labels for unknown classification: OTHER
t=2022-05-24 16:52:04,156 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-05-24 16:52:04,156 lvl=INFO msg=Dropped non public classification: GEO_PRIV
t=2022-05-24 16:52:04,156 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-05-24 16:52:04,157 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-05-24 16:52:04,157 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-05-24 16:52:04,157 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-05-24 16:52:04,157 lvl=INFO msg=Loaded service metadata
t=2022-05-24 16:52:04,158 lvl=INFO msg=Output files will be written in Cantabular 9.2.0 format
t=2022-05-24 16:52:04,159 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/cantabm_v9-2-0_unknown-metadata-version_dataset-md_20220524-1.json
t=2022-05-24 16:52:04,159 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/cantabm_v9-2-0_unknown-metadata-version_service-md_20220524-1.json
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
