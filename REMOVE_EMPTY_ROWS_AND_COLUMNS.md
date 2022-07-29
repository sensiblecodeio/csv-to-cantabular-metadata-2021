# Remove empty rows and columns utility

`bin/remove_empty_rows_and_columns.py` is a script for creating a transformed
copy of all CSV files in a given input path. The transformation removes empty
trailing columns (those without non-whitespace characters) and empty rows
(those without non-whitespace cell content).

The script is intended to tidy up CSV files created from Excel that can
sometimes contain additional empty cells where formatting has been applied
in Excel but there is no content etc.

Errors that cause transformation to stop:
- If the output directory contains files, the program will stop, unless
  the `--force-overwrite` flag is provided.
- Empty headings must be at the end, if the CSV file has an empty heading
  amongst others this is considered to be an unrecoverable error

Warnings will be logged (but processing will continue) when a data row:
- contains fewer cells than expected
- contains data in columns that are being removed

## Example usage
```
python3 bin/remove_empty_rows_and_columns.py -i <PATH_TO_CSV_DIRECTORY> -o <PATH_TO_OUTPUT_DIRECTORY>
```

- `-i` specifies the input directory containing the CSV files.
- `-o` specifies the output directory.
- `-f` specifies that the output directory need not be empty and that existing
       files in the output directory should be overwritten
