import csv
import os
import sys

input_dir = ''
if len(sys.argv) > 1:
    input_dir = sys.argv[1]

classifications = {}
with open(os.path.join(input_dir, 'Classification.csv'), newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        classifications[row['Classification_Mnemonic']] = row

categories = {}
with open(os.path.join(input_dir, 'Category.csv'), newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        classification_mnemonic = row['Classification_Mnemonic']
        if classification_mnemonic not in categories:
            categories[classification_mnemonic] = []
        categories[classification_mnemonic].append(row['Category_Code'])

for mnemonic, classification in classifications.items():
    expected_num_cats = int(classifications[mnemonic]['Number_Of_Category_Items'])
    if not expected_num_cats:
        continue

    cats = categories.get(mnemonic, [])
    if len(cats) != len(set(cats)):
        duplicate_codes = [c for c in cats if cats.count(c) > 1]
        print(f'Duplicate categories {duplicate_codes} found for classification {mnemonic}')

    if expected_num_cats and expected_num_cats != len(cats):
        print(f'Expected {expected_num_cats} categories for classification {mnemonic} but found {len(cats)}')

