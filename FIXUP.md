# Fixup script for 8th July 2022 release

`bin/fixup.py` is a script for fixing up the CSV files in the 8th July 2022 release.
The script addresses issues that cannot be handled by the `--best-effort` flag on `bin/ons_csv_to_ctb_json_main.py`.

It can be run as follows:
```
python3 bin/fixup.py -i <PATH_TO_CSV_DIRECTORY> -o modified/
```

`-i` specifies the input directory containing the CSV files.
`-o` specifies the output directory.

The `bin/ons_csv_to_ctb_json_main.py` script should then be run with the `-i` parameter pointing the the `modified` directory. The `--best-effort` flag is required due to other inconsistencies in the data.
```
python3 bin/ons_csv_to_ctb_json_main.py -i modified -o ctb_metadata_files/ --best-effort
```