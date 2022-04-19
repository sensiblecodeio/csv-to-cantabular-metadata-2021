Release Notes
=============

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

