Release Notes
=============

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

