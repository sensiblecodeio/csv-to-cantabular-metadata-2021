"""
Demo application for generating cantabular-metadata dataset file from CSV sources.

A Cantabular dataset corresponds to a database in the CSV sources.
"""

import csv
import json

DATABASE_FILE_NAME = "source/DATABASE.csv"
OUTPUT_FILE_NAME = "metadata/dataset-metadata.json"


def main():
    """Load database metadata from CSV file and convert to cantabular-metadata format."""
    datasets = list()
    print(f"Reading from {DATABASE_FILE_NAME}")
    for row in csv.DictReader(open(DATABASE_FILE_NAME, "r", encoding="utf-8-sig")):
        name = row["databaseMnemonic"]
        print(f'  Converting data for database "{name}" to Cantabular dataset metadata')
        datasets.append({
            "name": name,
            "meta": {
                "description": row["DESCRIPTION"]
            },
            "vars": []
        })

    print(f"Writing to {OUTPUT_FILE_NAME}")
    with open(OUTPUT_FILE_NAME, "w") as jsonfile:
        json.dump(datasets, jsonfile, indent=4)


if __name__ == "__main__":
    main()
