"""Interface for sending queries to metadata server."""

import json
from urllib.parse import urljoin
import requests


class MetadataServer:
    """MetadataServer allows communications with a Cantabular metadata server."""

    def __init__(self, metadata_url):
        """Initialise MetadataServer."""
        self.url = urljoin(metadata_url, 'graphql')

    def _query(self, graphql_query, graphql_variables=None):
        """Perform a GraphQL query and return the response."""
        http_resp = requests.post(self.url,
                                  data={'query': graphql_query,
                                        'variables': json.dumps(graphql_variables)})
        http_resp.raise_for_status()
        resp = http_resp.json()
        if 'errors' in resp:
            raise ValueError(f'error for {graphql_variables}')
        return resp

    def service_query(self):
        """Get the service metadata."""
        graphql_query = """
{
  en: service (lang: "en") {
    all
  }
  cy: service (lang: "cy") {
    all
  }
}
"""
        return self._query(graphql_query)

    def dataset_query(self, dataset):
        """Get the metadata for a dataset."""
        graphql_query = """
query($dataset: String!) {
 en: dataset(name: $dataset, lang: "en") {
   all
   description
   label
   name
 }
 cy: dataset(name: $dataset, lang: "cy") {
   all
   description
   label
   name
 }
}
"""
        return self._query(graphql_query, {'dataset': dataset})

    def table_query(self, table):
        """Get the metadata for a table."""
        graphql_query = """
query($table: String!) {
  en: service (lang: "en") {
    tables(names: [$table]) {
      name
      description
      label
      datasetName
      vars
      all
    }
  }
  cy: service (lang: "cy") {
    tables(names: [$table]) {
      name
      description
      label
      datasetName
      vars
      all
    }
  }
}
"""
        return self._query(graphql_query, {'table': table})

    def variable_query(self, dataset, variable):
        """Get the metadata for a variable."""
        graphql_query = """
query($dataset: String!, $variables: [String!]!) {
 en: dataset(name: $dataset, lang: "en") {
   vars(names: $variables) {
     name
     label
     description
     all
     catLabels
   }
 }
 cy: dataset(name: $dataset, lang: "cy") {
   vars(names: $variables) {
     name
     label
     description
     all
     catLabels
   }
 }
}
"""
        return self._query(graphql_query, {'dataset': dataset, 'variables': [variable]})
