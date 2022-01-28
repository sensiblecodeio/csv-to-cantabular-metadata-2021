`csv_to_metadata.py` is a simple script that shows how metadata can be loaded from CSV
files and converted to JSON format for loading into `cantabular-metadata`.

This repository does not contain any CSV source files. These files should be sourced independently
and placed in the `source` folder.

`csv_to_metadata.py` expects to find a file called `DATABASE.csv` in the `source` folder. This
file should contain one line per database and must have header fields called `DESCRIPTION` and
`databaseMnemonic`. A database in the CSV file is equivalent to a dataset in Cantabular terminology.

The script can be run by invoking it using `Python3` e.g.:
```
python3 csv_to_metadata.py
```

The script outputs a file in the `metadata` folder called `dataset-metadata.json`. The `metadata`
folder already contains a file called `metadata.graphql` that contains the GraphQL schema, and
another called `service-metadata.json` which contains metadata common to all datasets.

The files in the `metadata` folder can be loaded by `cantabular-metadata` (version 9.1.x) e.g.:
```
cd metadata
<PATH>/cantabular-metadata metadata.graphql service-metadata.json dataset-metadata.json
```

The metadata can be queried via a GraphQL interface. By default this is accessible at:

http://localhost:8493/graphql

`cantabular-metadata` is packaged with the [GraphiQL](https://github.com/graphql/graphiql) IDE
and this can be used to construct GraphQL queries when the service is accessed via a web browser.

The following query can be used to obtain information on a single dataset:

http://localhost:8493/graphql?query=%7Bdataset(name%3A%22UR%22)%7Bname%20meta%7Bdescription%7D%7D%7D