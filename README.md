Introduction
============

`bin/ons_csv_to_ctb_json_main.py` is an application that loads source metadata files in CSV format
and converts them to hierarchical JSON that can be loaded into `cantabular-metadata`.

It is compatible with version `1.0` of the metadata schema and version `9.3.0` of `cantabular-metadata`.

This is version `1.0.beta` of the CSV to JSON processing software and is subject to change.

The applications only use packages in the Python standard library.

Converting CSV to JSON
======================

Using test data
---------------

The `test/testdata` directory contains some sample CSV files that are used as part of continuous
integration testing. They contain dummy data that are intended to exercise the capabilities of the
software. The data can be used to verify the operation of `ons_csv_to_ctb_json_main.py`.

To convert the test CSV files in `test/testdata` to JSON files in `ctb_metadata_files/` run:
```
python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -o ctb_metadata_files/
```

Basic logging will be displayed by default, including the number of high-level Cantabular metadata
objects loaded and the name of the output files.
```
> python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -o ctb_metadata_files/
t=2022-04-06 14:46:15,321 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-04-06 14:46:15,321 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-04-06 14:46:15,321 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-04-06 14:46:15,322 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/dataset-metadata.json
t=2022-04-06 14:46:15,323 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-04-06 14:46:15,323 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-04-06 14:46:15,323 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/table-metadata.json
t=2022-04-06 14:46:15,324 lvl=INFO msg=Loaded service metadata
t=2022-04-06 14:46:15,324 lvl=INFO msg=Written service metadata file to: ctb_metadata_files/service-metadata.json

```

More detailed information can be obtained by running with a `-l DEBUG` flag e.g.:
```
> python3 bin/ons_csv_to_ctb_json_main.py -i test/testdata/ -o ctb_metadata_files/ -l DEBUG
t=2022-04-06 14:47:02,939 lvl=DEBUG msg=Creating classification for geographic variable: GEO2
t=2022-04-06 14:47:02,939 lvl=DEBUG msg=Loaded metadata for Cantabular variable: CLASS1
t=2022-04-06 14:47:02,939 lvl=DEBUG msg=Loaded metadata for Cantabular variable: CLASS2
t=2022-04-06 14:47:02,939 lvl=DEBUG msg=Loaded metadata for Cantabular variable: CLASS3
t=2022-04-06 14:47:02,939 lvl=DEBUG msg=Loaded metadata for Cantabular variable: GEO1
t=2022-04-06 14:47:02,939 lvl=INFO msg=Dropped non public classification: CLASS_PRIV
t=2022-04-06 14:47:02,939 lvl=DEBUG msg=Loaded metadata for Cantabular variable: GEO2
t=2022-04-06 14:47:02,939 lvl=INFO msg=Loaded metadata for 5 Cantabular variables
t=2022-04-06 14:47:02,939 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: DB1
t=2022-04-06 14:47:02,939 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: DB2
t=2022-04-06 14:47:02,940 lvl=DEBUG msg=Loaded metadata for Cantabular dataset: DB3
t=2022-04-06 14:47:02,940 lvl=INFO msg=Loaded metadata for 3 Cantabular datasets
t=2022-04-06 14:47:02,941 lvl=INFO msg=Written dataset metadata file to: ctb_metadata_files/dataset-metadata.json
t=2022-04-06 14:47:02,941 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS1
t=2022-04-06 14:47:02,941 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS2
t=2022-04-06 14:47:02,941 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS3
t=2022-04-06 14:47:02,941 lvl=INFO msg=Dropped non public ONS Dataset: DS_PRIV
t=2022-04-06 14:47:02,941 lvl=DEBUG msg=Loaded metadata for Cantabular table: DS4
t=2022-04-06 14:47:02,941 lvl=INFO msg=Loaded metadata for 4 Cantabular tables
t=2022-04-06 14:47:02,942 lvl=INFO msg=Written table metadata file to: ctb_metadata_files/table-metadata.json
t=2022-04-06 14:47:02,942 lvl=INFO msg=Loaded service metadata
```

Using externally sourced files
------------------------------

To convert the externally sourced metadata CSV files currently being used for testing, first fixup the source files:
```
python3 bin/fixup.py -i <SOURCE_DIRECTORY> -o modified/
```

This will load the sample files and modify them slightly so that they can be processed by `ons_csv_to_ctb_json_main.py`. This step will not be needed for production.

Then convert the files to JSON:
```
python3 bin/ons_csv_to_ctb_json_main.py -i modified/ -o ctb_metadata_files/
```

Load the JSON files with cantabular-metadata
============================================

To load the generated JSON files into `cantabular-metadata` (version 9.3.0) run:
```
cd ctb_metadata_files
CANTABULAR_METADATA_GRAPHQL_TYPES_FILE=metadata.graphql CANTABULAR_METADATA_SERVICE_FILE=service-metadata.json CANTABULAR_METADATA_DATASET_FILES=dataset-metadata.json CANTABULAR_METADATA_TABLE_FILES=table-metadata.json <PATH_TO_BINARY>/cantabular-metadata
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
-----

This repository has tests written using the `unittest` framework. They are run as part of
Continuous Integration testing in the GitHub repository. They can be run manually by running this
command from the base directory:

```
PYTHONPATH=test:bin python3 -m unittest -v
```
