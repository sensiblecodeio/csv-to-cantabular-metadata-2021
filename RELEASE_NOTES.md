Release Notes
=============

1.2.gamma
-----------
- Ensure input files to `remove_empty_rows_and_columns.py` are processed in a repeatable
  order. This fixes an issue where unit tests might incorrectly fail on some systems.

1.2.1-alpha
-----------
- Added utility `remove_empty_rows_and_columns.py` to remove any empty rows and
  columns from all CSV files in a given directory and write the modified files
  to a specified output directory.

1.2.alpha
---------
- Updated code to work with metadata schema version 1.2.
- Cantabular version 10.1.0 is now the default version. The file format for version 10.1.0 and
  10.0.0 are identical.

1.1.delta
---------
- Cantabular version 10.0.0 is now the default version. The file format for version 10.0.0 and
  9.3.0 are identical.
- Use the Codebook_Mnemonic from Category_Mapping.csv as the variable name.
- Drop the Parent_Classification_Mnemonic from VariableMetadata in the GraphQL schema. This
  information can be obtained from the codebook and its contents are ambiguous since a variable
  name can now be either the Classification_Mnemonic or Codebook_Mnemonic.

1.1.gamma
---------
- In `--best-effort` mode don't drop tables (ONS datasets) which use variables (ONS classifications) that
  are not listed as belonging to the table dataset (ONS database).

1.1.beta
--------
- Added `--best-effort` flag to discard invalid data and make a best effort
  attempt to generate output files.
  - This replaces the `fixup.py` script.
- Formatted and customizable output filenames.
- Support for Cantabular version 9.2.0 formatting.
- Rework on mandatory fields.
- Added 2011 1% sample metadata.

1.1.alpha
---------
- Updated code to work with metadata schema version 1.1.
- Updated fixup.py script to work with latest drop of CSV source files.

1.0.gamma
---------
- Categories for geographic variables are read from a separate lookup file which is specified
  using the `-g` flag.
  - No categories for geographic variables will be loaded if a geography lookup file is not
    specified.
  - Categories for geographic variables must not be specified in the main set of CSV files.
- Classifications are automatically created for geographic variables.
  - The classification will have the same name as the variable.
  - The main set of CSV files must not contain classifications for geographic variables.
- Added logging to fixup.py
- The built-in descriptions fields for variables and datasets are now populated.

1.0.beta
--------
- Supports Cantabular version 9.3.0
  - Tables are now a built-in concept in `cantabular-metadata` and are written to their own JSON file
  - The generated JSON files must now be supplied to `cantabular-metadata` via environment variables
  - Every table must have at least one variable (geographic or non-geographic)
- Clearer error message if invalid directories supplied to ons_csv_to_ctb_json_main.py

1.0.alpha
---------
- Supports metadata schema version 1.0
- Supports Cantabular version 9.2.0

