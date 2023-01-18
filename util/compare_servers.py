"""
Check that datasets on two different instances on cantabular-metadata are the same.

Script leverages the unittest infrastructure and validates that the datasets and variables
on two separate instances of cantabular-metadata are the same. The dataset and variable names
are identified by parsing CSV metadata source files.

Environment variables can be used to set the CSV files directory and the URLs of the metadata
servers.

The tests are split into a number of suites and there are individual tests for English and
Welsh versions.

Some examples of running tests are shown below:

    Run all tests:
    python3 compare_servers.py
    OR
    python3 compare_servers.py

    Run only Welsh tests:
    python3 compare_servers.py DatasetTests CatLabelTests VariableTests -k _cy_


    Run only English tests in CatLabelTests suite:
    python3 compare_servers.py CatLabelTests -k _en_
"""

import csv
import json
import unittest
import os
import requests

CSV_FILES_DIR = os.environ.get('CTB_TEST_CSV_FILES_DIR', './')
SERVER1_URL = os.environ.get('CTB_TEST_SERVER1_URL', 'http://127.0.0.1:8493/graphql')
SERVER2_URL = os.environ.get('CTB_TEST_SERVER2_URL', 'http://127.0.0.2:8493/graphql')

DATASET_QUERY = """
query($dataset: String!, $lang: String!) {
 dataset(name: $dataset, lang: $lang) {
   all
   description
   label
   name
 }
}
"""

VARIABLE_QUERY = """
query($variables: [String!]!, $lang: String!) {
 dataset(name: "base", lang: $lang) {
   vars(names: $variables) {
     name
     label
     description
     all
   }
 }
}
"""

CAT_LABELS_QUERY = """
query($variables: [String!]!, $lang: String!) {
 dataset(name: "base", lang: $lang) {
   vars(names: $variables) {
     catLabels
   }
 }
}
"""

def get_variables():
    """
    Identify all the Cantabular variables from a set of CSV metadata files.

    Cantabular variable names are the set of Codebook_Mnemonic values from Category_Mapping.csv
    along with the Variable_Mnemonic values from Variable.csv for geographic variables.
    """
    variables = set()
    with open(os.path.join(CSV_FILES_DIR, 'Category_Mapping.csv'), encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            variables.add(row['Codebook_Mnemonic'])

    with open(os.path.join(CSV_FILES_DIR, 'Variable.csv'), encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Variable_Type_Code'] == 'GEOG':
                variables.add(row['Variable_Mnemonic'])

    return sorted(list(variables))


def get_datasets():
    """
    Identify all the Cantabular datasets from a set of CSV metadata files.

    Cantabular dataset names are the set of Database_Mnemonic values from Databases.csv.
    """
    datasets = []
    with open(os.path.join(CSV_FILES_DIR, 'Database.csv'), encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            datasets.append(row['Database_Mnemonic'])

    return sorted(datasets)


class TestsContainer(unittest.TestCase):
    """TestsContainer holds dynamically created unit test cases."""

    longMessage = True

    def query(self, url, graphql_query, graphql_variables):
        """Perform a GraphQL query and return the response."""
        http_resp = requests.post(url,
                                  data={'query': graphql_query,
                                        'variables': json.dumps(graphql_variables)})
        http_resp.raise_for_status()
        resp = http_resp.json()
        self.assertNotIn('errors', resp)
        return resp


class DatasetTests(TestsContainer):
    """Tests that compare datasets."""


class VariableTests(TestsContainer):
    """Tests that compare variables."""


class CatLabelTests(TestsContainer):
    """Tests that compare category labels for a variable."""


def make_test_function(graphql_query, graphql_variables):
    """Make a test function and add it to the TestsContainer class."""
    def test(self):
        resp1 = self.query(SERVER1_URL, graphql_query, graphql_variables)
        resp2 = self.query(SERVER2_URL, graphql_query, graphql_variables)
        self.assertDictEqual(resp1, resp2)
    return test


if __name__ == '__main__':
    for dataset in get_datasets():
        test_func = make_test_function(DATASET_QUERY, {'dataset': dataset, 'lang': 'en'})
        setattr(DatasetTests, f'test_en_dataset{dataset}', test_func)

        test_func = make_test_function(DATASET_QUERY, {'dataset': dataset, 'lang': 'cy'})
        setattr(DatasetTests, f'test_cy_dataset{dataset}', test_func)

    for variable in get_variables():
        test_func = make_test_function(VARIABLE_QUERY, {'variables': [variable], 'lang': 'en'})
        setattr(VariableTests, f'test_en_variable_{variable}', test_func)

        test_func = make_test_function(VARIABLE_QUERY, {'variables': [variable], 'lang': 'cy'})
        setattr(VariableTests, f'test_cy_variable_{variable}', test_func)

        test_func = make_test_function(CAT_LABELS_QUERY, {'variables': [variable], 'lang': 'en'})
        setattr(CatLabelTests, f'test_en_variable_{variable}', test_func)

        test_func = make_test_function(CAT_LABELS_QUERY, {'variables': [variable], 'lang': 'cy'})
        setattr(CatLabelTests, f'test_cy_variable_{variable}', test_func)


if __name__ == '__main__':
    unittest.main()
