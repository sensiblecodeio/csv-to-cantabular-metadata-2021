# 2021 census metadata in Cantabular

The scripts in this repository convert census metadata in CSV format to JSON files
which serve as the input to the Cantabular metadata service, `cantabular-metadata`.

The metadata schema has changed slightly between different versions of Cantabular.
This document covers the current version of Cantabular (**10.0.0**). The scripts also
provide support for generating JSON files that are compatible with some legacy versions.

`cantabular-metadata` allows metadata for one or more datasets in a companion
`cantabular-server` service to be loaded and made available to query by `cantabular-ui`
and other software accessing its API directly.

`cantabular-metadata` uses GraphQL for its API, which allows
`cantabular-ui` and any other API consumers to request only the
fields of metadata that are needed for their purpose.

The schema of the metadata loaded into the service can be customised
at runtime by supplying a GraphQL schema file along with the metadata
content, allowing for a wide variety of metadata to be loaded.

The software allows metadata to be attached to:
 - a **service** (which serves a collection of datasets)
 - the **datasets** associated with the service (from which tables can be built using queries)
 - the **variables** which exist in each dataset
 - pre-defined **tables** within the service

Metadata can be loaded in multiple languages by specifying a
language parameter on input metadata JSON. This allows other software that
makes use of the metadata service to be supplied with localised reference
metadata, where relevant, for all metadata types.

# Processing 2021 census metadata

## CSV metadata files

The raw metadata are provided as a set of CSV files, the format and arrangement of which has been
specified by the ONS.

The CSV files contain metadata for:
 - **databases** which correspond to Cantabular **datasets**
 - **datasets** which correspond to Cantabular **tables**
 - **variables** and **classifications**
    - Classifications can be thought of as concrete implementations of abstract variables.
      Each classification has a set of associated **categories**.
    - Classifications are equivalent to Cantabular **variables**.

Data from the CSV files are mapped to values in built-in `cantabular-metadata` objects and to
user defined objects. The names of user-defined objects have been chosen to reflect the names of
the source file names wherever possible. The field names within the user defined objects have also
been chosen to reflect the column names in the source files.

The source files contain some fields that are Welsh equivalents of other fields. The metadata service
has separate objects for English and Welsh versions of the high level metadata objects.

If an optional Welsh field is not populated, then the English version will typically be used in its place.

The source files can have English and Welsh category labels. Only Welsh labels are included in the
output JSON because the English labels can be obtained from the codebook.

The `Codebook_Mnemonic` for each classification is extracted from `Category_Mapping.csv` but the other fields are ignored.

The data in `Specification.csv`, `Specification_Type.csv`, `Asset_Child_Reference.csv`, `Asset_Reference.csv`
and `Metadata_Version.csv` are not processed.

## Geography lookup file

The main set of CSV files does not contain category information for geographic variables. A separate geography
lookup file contains this information. These Python scripts extract the Welsh category labels for geographic
variables from this file.

# `cantabular-metadata` schema

This section describes the `cantabular-metadata` schema and how fields in the output are
derived from the source files. A table is provided for each object which details the field name,
the [GraphQL](https://graphql.org/learn/schema/) type and the sources for the English and Welsh versions of the metadata.

Where the "Source (en)" or "Source (cy)" columns have a value such as `Dataset.Dataset_Mnemonic` this
means that the source is the `Dataset_Mnemonic` field in the appropriate row of the `Dataset.csv` file.

## Service

The `Service` object is a built-in type in `cantabular-metadata`. It contains information that
is relevant to all the datasets that are hosted by an instance of `cantabular-server`.

It consists of a `ServiceMetadata` object which contains user defined fields, and a list of `Table`
objects where each entry corresponds to a table specified in `Dataset.csv`.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `meta` | `ServiceMetadata!` | | |
| `tables` | `[Table!]` | Tables read from `Dataset.csv` | |

## ServiceMetadata

All the fields in `ServiceMetadata` are user defined. The census metadata consists of data that is
relevant on a per dataset basis, so this object only has a `description` field containing a preset
message.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `description` | `String!` | "Census 2021 metadata" | "Census 2021 metadata in Welsh" |

## Table

A Cantabular table is equivalent to an ONS dataset.

The `Table` object is a built-in type in `cantabular-metadata`. The `name`, `label` and `description`
fields are sourced from `Dataset.csv`. The other fields in the file are contained in the `TableMetadata`
object.

Only tables with a value of `PUB` (i.e. public) in `Dataset.Security_Mnemonic` are included in the
Cantabular metadata.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `name` | `String!` | `Dataset.Dataset_Mnemonic` | |
| `label` | `String` | `Dataset.Dataset_Title` | `Dataset.Dataset_Title_Welsh` |
| `description` | `String` | `Dataset.Dataset_Description` | `Dataset.Dataset_Description_Welsh` |
| `datasetName` | `String` | `Dataset.Database_Mnemonic` | |
| `meta` | `TableMetadata!` | Additional data from `Dataset.csv` | |
| `vars` | `[String!]!` | Table variable names sourced from `Dataset_Variable.csv` (see note below) | |

`vars` is sourced from `Dataset_Variable.csv` and is a list of names of Cantabular variables that are
used to construct the table. The variable names are sorted using the `Processing_Priority` value in
`Dataset_Variable`. Zero or more geographic variables can be specified for a single table in `Dataset_Variable.csv`.
`vars` will contain at most one geographic variable. This will be the first element on the list and will
be the geographic variable in `Dataset_Variable.csv` which has `Lowest_Geog_Variable_Flag` set to `Y`.
All other geographic variables are listed in `TableMetadata.Alternate_Geographic_Variables`.

## TableMetadata

All the fields in `TableMetadata` are user defined. It contains information from `Dataset.csv` that
is not included in the `Table` object.

The object also contains data from `Related_Datasets.csv`, `Dataset_Keyword.csv`, `Publication_Dataset.csv`
and `Release_Dataset.csv`.

The `Signed_Off_Flag` and `Id` field in `Classification.csv` are ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Dataset_Mnemonic_2011` | `String` | `Dataset.Dataset_Mnemonic_2011` | |
| `Geographic_Coverage` | `String!` | `Dataset.Geographic_Coverage` | `Dataset.Geographic_Coverage_Welsh` |
| `Dataset_Population` | `String!` | `Dataset.Dataset_Population` | `Dataset.Population_Welsh` |
| `Last_Updated` | `String` | `Dataset.Last_Updated` | |
| `Unique_Url` | `String` | `Dataset.Unique_Url` | |
| `Contact` | `Contact` | Keyed on `Dataset.Contact_Id` | |
| `Version` | `String!` | `Dataset.Version` | |
| `Related_Datasets` | `[String]!` | List of `Related_Datasets.Related_Dataset_Mnemonic` values keyed on `Related_Datasets.Dataset_Mnemonic` | |
| `Keywords` | `[String]!` | List of `Dataset_Keyword.Dataset_Keyword` values keyed on `Dataset_Keyword.Dataset_Mnemonic` | List of `Dataset_Keyword.Dataset_Keyword_Welsh` values keyed on `Dataset_Keyword.Dataset_Mnemonic` |
| `Publications` | `[Publication]!` | List of `Publication` values keyed on `Publication_Dataset.Dataset_Mnemonic` | |
| `Census_Releases` | `[Census_Release]!` | List of `Census_Release` values keyed on `Release_Dataset.Dataset_Mnemonic`/`Census_Release_Number`| |
| `Statistical_Unit` | `Statistical_Unit!` | Keyed on `Dataset.Statistical_Unit` | |
| `Alternate_Geographic_Variables` | `[String!]` | List of alternate geographic variable names which are available for this table sourced from `Dataset_Variable.csv` keyed on `Dataset_Variable.Dataset_Mnemonic` | |

## Dataset

The `Dataset` object is a built-in type in `cantabular-metadata`. The `name`, `label` and `description`
fields are sourced from `Database.csv`. The other fields in the file are contained in the `DatasetMetadata`
object.

All the variables in the metadata have been added to a base dataset, which all other datasets include.
This significantly reduces the size of the JSON file containing the dataset information.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `name` | `String!` | `Database.Database_Mnemonic` | |
| `label` | `String` | `Database.Database_Title` | `Database.Database_Title_Welsh` |
| `description` | `String` | `Database.Description` | `Database.Database_Description_Welsh` |
| `meta` | `DatasetMetadata!` | Additional fields from `Database.csv` | |
| `vars` | `[Variable]!` | List of `Variable` objects read from `Classification.csv` | |

## DatasetMetadata

All the fields in `DatasetMetadata` are user defined. It contains information from `Database.csv` that is not included
in the `Dataset` object.

The `Lowest_Geog_Variable` value is identified from the relevant entries in `Database_Variable.csv`.

The `Id` and `IAR_Asset_Id` fields in `Database.csv` are ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Cantabular_DB_Flag` | `String` | `Database.Cantabular_DB_Flag` | |
| `Source` | `Source!` | Keyed on `Database.Source_Mnemonic` | |
| `Version` | `String!` | `Database.Version` | |
| `Lowest_Geog_Variable` | `String` | `Database_Variable.Variable_Mnemonic` for entry in `Database_Variable.csv` with a `Database_Variable.Lowest_Geog_Variable_Flag` value of `Y` | |

## Variable

A Cantabular variable is equivalent to a census classification. Each census classification has an associated
census variable. The source CSV files do not define classifications for geographic variables. The scripts in
this repository therefore automatically create classifications for geographic variables.

The `Variable` object is a built-in type in `cantabular-metadata`. The `name`, `label` and `description` are populated
from appropriate values in `Classification.csv` or `Variable.csv`.

Only variables with a value of `PUB` (i.e. public) in `Classification.Security_Mnemonic` are included in the
Cantabular metadata.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `name` | `String!` | See note below | |
| `label` | `String` | `Classification.External_Classification_Label_English` or `Variable.Variable_Title` for geographic variables | `Classification.External_Classification_Label_Welsh` or `Variable.Variable_Title_Welsh` for geographic variables |
| `description` | `String` | `Variable.Variable_Description` | `Variable.Variable_Description_Welsh`. |
| `meta` | `VariableMetadata!` | User specific metadata from `Classification.csv` | |
| `catLabels` | `LabelsMap` | `{}` | Map of `Category.Code` to `Category.External_Category_Label_Welsh` values (see note below) |
| `digest` | `String!` | Automatically populated hash of values in metadata for the variable | |

It is essential that the variable `name` matches the name of the variable in the Cantabular codebook. For
non-geographic variables this will be `Category_Mapping.Codebook_Mnemonic` if the field is populated for
the classification or else `Classification.Classification_Mnemonic`. For base classifications the `Codebook_Mnemonic` and `Classification_Mnemonic` are likely to be different, whereas for higher level
classifications they will be the same. The `name` will be `Variable.Variable_Mnemonic` for geographic variables.

The English version of `catLabels` is an empty map. The English labels can be sourced from the codebook. The Welsh
version of `catLabels` is a map of category codes to Welsh labels. It only contains values for Welsh labels that are
populated i.e. it is not necessarily an exhaustive list of variable categories.

## VariableMetadata

All the fields in `VariableMetadata` are user defined. It contains information from `Classification.csv` that
is not included in the `Variable` object. As noted above, classifications for geographic variables are automatically
created and this is reflected in the values in this object.

The `Parent_Classification_Mnemonic`, `Signed_Off_Flag`, `Flat_Classification_Flag` and `Id` field in `Classification.csv` are ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Mnemonic_2011` | `String` | `Classification.Mnemonic_2011` or `null` for geographic variables | |
| `Default_Classification_Flag` | `String` | `Classification.Default_Classification_Flag` or `null` for geographic variables | |
| `Version` | `String!` | `Classification.Version` or `Variable.Version` for geographic variables | |
| `ONS_Variable` | `ONS_Variable!` | Keyed on `Classification.Variable_Mnemonic` or `Variable.Variable_Mnemonic` for geographic variables | |
| `Topics` | `[Topic]!` | List of `Topic` values keyed on `Topic_Classification.Classification_Mnemonic`/`Topic_Mnemonic` or `[]` for geographic variables | |

## ONS_Variable

`ONS_Variable` is a user defined object.

The data is sourced from `Variable.csv`.

The `Id`, `Signed_Off_Flag` and `Number_Of_Classifications` fields in `Variable.csv` are ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Variable_Mnemonic` | `String!` | `Variable.Variable_Mnemonic` | |
| `Variable_Title` | `String!` | `Variable.Variable_Title` | `Variable.Variable_Title_Welsh`|
| `Variable_Mnemonic_2011` | `String` | `Variable.Variable_Mnemonic_2011` | |
| `Comparability_Comments` | `String` | `Variable.Comparability_Comments` | `Variable.Comparability_Comments_Welsh` |
| `Uk_Comparison_Comments` | `String` | `Variable.Uk_Comparison_Comments` | `Variable.Uk_Comparison_Comments_Welsh` |
| `Geographic_Abbreviation` | `String` | `Variable.Geographic_Abbreviation` | `Variable.Geographic_Abbreviation_Welsh` |
| `Geographic_Theme` | `String` | `Variable.Geographic_Theme` | `Variable.Geographic_Theme_Welsh` |
| `Geographic_Coverage` | `String` | `Variable.Geographic_Coverage` | `Variable.Geographic_Coverage_Welsh` |
| `Version` | `String!` | `Variable.Version` | |
| `Statistical_Unit` | `Statistical_Unit` | Keyed on `Variable.Statistical_Unit` | |
| `Keywords` | `[String]!` | List of `Variable_Keyword.Variable_Keyword` values keyed on `Variable_Keyword.Variable_Mnemonic` | List of `Variable_Keyword.Variable_Keyword_Welsh` values keyed on `Variable_Keyword.Variable_Mnemonic`|
| `Topic` | `Topic` | Keyed on `Variable.Topic_Mnemonic` | |
| `Questions` | `[Question]!` | List of `Question` keyed on `Variable.Source_Question.Variable_Mnemonic`/`Source_Question_Code` | |
| `Variable_Type` | `Variable_Type!` | `Variable.Variable_Type_Code` | |
| `Quality_Statement_Text` | `String` | `Variable.Quality_Statement_Text` | |
| `Quality_Summary_URL` | `String` | `Variable.Quality_Summary_URL` | |

## Variable_Type

The data is sourced from `Variable_Type.csv`. The `Id` field in `Variable_Type.csv` is ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Variable_Type_Code` | `String!` | `Variable_Type.Variable_Type_Code` | |
| `Variable_Type_Description` | `String!` | `Variable_Type.Variable_Type_Description` | `Variable_Type.Variable_Type_Description_Welsh` |

## Topic

The data is sourced from `Topic.csv`. The `Id` field in `Topic.csv` is ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Topic_Mnemonic` | `String!` | `Topic.Topic_Mnemonic` | |
| `Topic_Description` | `String!` | `Topic.Topic_Description` | `Topic.Topic_Description_Welsh` |
| `Topic_Title` | `String!` | `Topic.Topic_Title` | `Topic.Topic_Title_Welsh` |

## Question

The data is sourced from `Question.csv`. The `Id` field in `Question.csv` is ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Question_Code` | `String!` | `Question.Question_Code` | |
| `Question_Label` | `String!` | `Question.Question_Label` | `Question.Question_Label_Welsh` |
| `Reason_For_Asking_Question` | `String` | `Question.Reason_For_Asking_Question` | `Question.Reason_For_Asking_Question_Welsh` |
| `Question_First_Asked_In_Year` | `String` | `Question.Question_First_Asked_In_Year` | |
| `Version` | `String!` | `Question.Version` | |

## Source

The data is sourced from `Source.csv`. The `Id` field in `Source.csv` is ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Source_Mnemonic` | `String!` | `Source.Source_Mnemonic` | |
| `Source_Description` | `String!` | `Source.Source_Description` | `Source.Source_Description_Welsh` |
| `Copyright_Statement` | `String` | `Source.Copyright_Statement` | |
| `Licence` | `String` | `Source.Licence` | |
| `Nationals_Statistic_Certified` | `String` | `Source.Nationals_Statistic_Certified` | |
| `Methodology_Link` | `String` | `Source.Methodology_Link` | |
| `Methodology_Statement` | `String` | `Source.Methodology_Statement` | `Source.Methodology_Statement_Welsh` |
| `SDC_Link` | `String` | `Source.SDC_Link` | |
| `SDC_Statement` | `String` | `Source.SDC_Statement` | `Source.SDC_Statement_Welsh` |
| `Version` | `String!` | `Source.Version` | |
| `Contact` | `Contact` | Keyed on `Source.Contact_Id` | |

## Contact

The data is sourced from `Contact.csv`.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Contact_Id` | `String!` | `Contact.Contact_Id` | |
| `Contact_Name` | `String!` | `Contact.Contact_Name` | |
| `Contact_Email` | `String!` | `Contact.Contact_Email` | |
| `Contact_Phone` | `String` | `Contact.Contact_Phone` | |
| `Contact_Website` | `String` | `Contact.Contact_Website` | |

## Publication

The data is sourced from  `Publication_Dataset.csv`. The `Dataset_Mnemonic` field in
`Publication_Dataset.csv` is used to identify publications associated with each table.

The `Id` field in `Publication_Dataset.csv` is ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Publication_Mnemonic` | `String!` | `Publication_Dataset.Publication_Mnemonic` | |
| `Publication_Title` | `String` | `Publication_Dataset.Publication_Title` | |
| `Publisher_Name` | `String` | `Publication_Dataset.Publisher_Name` | |
| `Publisher_Website` | `String` | `Publication_Dataset.Publisher_Website` | |

## Census_Release

The data is sourced from `Census_Release.csv`. The `Id` field in `Census_Release.csv` is ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Census_Release_Number` | `String!` | `Census_Release.Census_Release_Number` | |
| `Census_Release_Description` | `String!` | `Census_Release.Census_Release_Description` | |
| `Release_Date` | `String!` | `Census_Release.Release_Date` | |

## Statistical_Unit

The data is sourced from `Statistical_Unit.csv`. The `Id` field in `Statistical_Unit.csv` is ignored.

| Field | GraphQL Type | Source (en) | Source (cy) |
| --- | --- | --- | --- |
| `Statistical_Unit` | `String!` | `Statistical_Unit.Statistical_Unit` | |
| `Statistical_Unit_Description` | `String!` | `Statistical_Unit.Statistical_Unit_Description` | `Statistical_Unit.Statistical_Unit_Description_Welsh` |


# Sample queries

This section contains some examples of GraphQL queries that can be used to query metadata for the
dataset named `Teaching-Dataset` from `cantabular-metadata` and `cantabular-api-ext`. Sample responses
have also been provided.

## `cantabular-metadata` queries

### Get all tables

This query gets the `name` value for every table in the metadata.

#### Query

```
{
  service {
    tables {
      name
    }
  }
}
```

#### Response

```
{
  "data": {
    "service": {
      "tables": [
        {
          "name": "LC1117EW"
        },
        {
          "name": "LC2101EW"
        },
        {
          "name": "LC2107EW"
        },
        {
          "name": "LC6107EW"
        },
        {
          "name": "LC6112EW"
        }
      ]
    }
  }
}
```

### Get metadata for one table

This query gets additional metadata for a single table named **LC1117EW**.

#### Query

```
{
  service {
    tables(names: ["LC1117EW"]) {
      name
      label
      description
      meta {
        Alternate_Geographic_Variables
        Statistical_Unit {
          Statistical_Unit_Description
        }
      }
      datasetName
      vars
    }
  }
}
```

#### Response

```
{
  "data": {
    "service": {
      "tables": [
        {
          "datasetName": "Teaching-Dataset",
          "description": "This dataset provides 2011 Census estimates that classify usual residents by sex, and by age (ages 0 to 15 grouped together, 10 year age groups up to 74 then 75 years and over grouped together). The estimates are as at census day, 27 March 2011.",
          "label": "Sex by age",
          "meta": {
            "Alternate_Geographic_Variables": [
              "Country"
            ],
            "Statistical_Unit": {
              "Statistical_Unit_Description": "People living in England and Wales"
            }
          },
          "name": "LC1117EW",
          "vars": [
            "Region",
            "Sex",
            "Age"
          ]
        }
      ]
    }
  }
}
```

### Get metadata for a dataset and its variables

This query gets some metadata for a specific dataset named **Teaching-Dataset** along
with metadata for the **Region** and **Sex** variables.

#### Query

```
{
  dataset(name: "Teaching-Dataset") {
    name
    description
    meta {
      Lowest_Geog_Variable
    }
    vars(names: ["Region", "Sex"]){
      catLabels
      description
      meta {
        Topics {
          Topic_Mnemonic
          Topic_Description
        }
      }
    }
  }
}
```

#### Response

```
{
  "data": {
    "dataset": {
      "description": "An anonymised random sample of 1% of people from the 2011 Census for England and Wales, including both usual residents and short-term residents.",
      "meta": {
        "Lowest_Geog_Variable": "Region"
      },
      "name": "Teaching-Dataset",
      "vars": [
        {
          "catLabels": null,
          "description": "The geographic region in which a person lives, derived from the address of their household or communal establishment.",
          "meta": {
            "Topics": []
          }
        },
        {
          "catLabels": null,
          "description": "The classification of a person as either male or female.",
          "meta": {
            "Topics": [
              {
                "Topic_Description": "Data and analysis on migration patterns, age structure and families.",
                "Topic_Mnemonic": "MAD"
              }
            ]
          }
        }
      ]
    }
  }
}
```

### Get metadata for a dataset and its variables in Welsh

This query requests the same information as requested in the previous query but in Welsh.

#### Query

```
{
  dataset(name: "Teaching-Dataset" lang: "cy") {
    name
    description
    meta {
      Lowest_Geog_Variable
    }
    vars(names: ["Region", "Sex"]){
      catLabels
      description
      meta {
        Topics {
          Topic_Mnemonic
          Topic_Description
        }
      }
    }
  }
}
```

#### Response

```
{
  "data": {
    "dataset": {
      "description": "Sampl ddienw ar hap o 1% o bobl o Gyfrifiad 2011 ar gyfer Cymru a Lloegr, gan gynnwys preswylwyr arferol a thrigolion tymor byr.",
      "meta": {
        "Lowest_Geog_Variable": "Region"
      },
      "name": "Teaching-Dataset",
      "vars": [
        {
          "catLabels": {
            "E12000001": "Gogledd Ddwyrain",
            "E12000002": "Gogledd Orllewin",
            "E12000003": "Swydd Efrog a'r Humber",
            "E12000004": "Dwyrain Canolbarth Lloegr",
            "E12000005": "Gorllewin Canolbarth Lloegr",
            "E12000006": "Dwyrain Lloegr",
            "E12000007": "Llundain",
            "E12000008": "De Ddwyrain",
            "E12000009": "De Orllewin",
            "W92000004": "Cymru"
          },
          "description": "Y rhanbarth daearyddol y mae person yn byw ynddo, yn deillio o gyfeiriad eu cartref neu sefydliad cymunedol.",
          "meta": {
            "Topics": []
          }
        },
        {
          "catLabels": {
            "1": "Gwryw",
            "2": "Benyw"
          },
          "description": "Dosbarthiad person naill ai'n wryw neu'n fenyw.",
          "meta": {
            "Topics": [
              {
                "Topic_Description": "Data a dadansoddiad ar batrymau mudo, strwythur oedran a theuluoedd.",
                "Topic_Mnemonic": "MAD"
              }
            ]
          }
        }
      ]
    }
  }
}
```

## `cantabular-api-ext` queries

`cantabular-api-ext` combines information from `cantabular-server` and `cantabular-metadata`.

### Perform tabulation and get metadata

This query requests a tabulation of the **country** and **sex** variables in the **Teaching-Dataset**.
It also requests some metadata for the dataset, variables and **LC1117EW** table.

#### Query

```
{
  service {
    tables(names: "LC1117EW") {
      description
    }
  }
  dataset(name: "Teaching-Dataset") {
    name
    description
    meta {
      Lowest_Geog_Variable
    }
    table(variables: ["country", "sex"]) {
      values
      dimensions {
        categories {
          code
          label
        }
      }
    }
  }
}
```

#### Response

```
{
  "data": {
    "dataset": {
      "description": "An anonymised random sample of 1% of people from the 2011 Census for England and Wales, including both usual residents and short-term residents.",
      "meta": {
        "Lowest_Geog_Variable": "Region"
      },
      "name": "Teaching-Dataset",
      "table": {
        "dimensions": [
          {
            "categories": [
              {
                "code": "E",
                "label": "England"
              },
              {
                "code": "W",
                "label": "Wales"
              }
            ]
          },
          {
            "categories": [
              {
                "code": "1",
                "label": "Male"
              },
              {
                "code": "2",
                "label": "Female"
              }
            ]
          }
        ],
        "values": [
          265262,
          273502,
          15307,
          15670
        ]
      }
    },
    "service": {
      "tables": [
        {
          "description": "This dataset provides 2011 Census estimates that classify usual residents by sex, and by age (ages 0 to 15 grouped together, 10 year age groups up to 74 then 75 years and over grouped together). The estimates are as at census day, 27 March 2011."
        }
      ]
    }
  }
}
```

### Perform query and get metadata in Welsh

This query asks for the same information as the previous query but in Welsh.

#### Query

```
{
  service(lang: "cy") {
    tables(names: "LC1117EW") {
      description
    }
  }
  dataset(name: "Teaching-Dataset", lang: "cy") {
    name
    description
    meta {
      Lowest_Geog_Variable
    }
    table(variables: ["country", "sex"]) {
      values
      dimensions {
        categories {
          code
          label
        }
      }
    }
  }
}
```

#### Response

```
{
  "data": {
    "dataset": {
      "description": "Sampl ddienw ar hap o 1% o bobl o Gyfrifiad 2011 ar gyfer Cymru a Lloegr, gan gynnwys preswylwyr arferol a thrigolion tymor byr.",
      "meta": {
        "Lowest_Geog_Variable": "Region"
      },
      "name": "Teaching-Dataset",
      "table": {
        "dimensions": [
          {
            "categories": [
              {
                "code": "E",
                "label": "Lloegr"
              },
              {
                "code": "W",
                "label": "Cymru"
              }
            ]
          },
          {
            "categories": [
              {
                "code": "1",
                "label": "Gwryw"
              },
              {
                "code": "2",
                "label": "Benyw"
              }
            ]
          }
        ],
        "values": [
          265262,
          273502,
          15307,
          15670
        ]
      }
    },
    "service": {
      "tables": [
        {
          "description": "Mae'r set ddata hon yn darparu amcangyfrifon Cyfrifiad 2011 sy'n dosbarthu preswylwyr arferol yn ôl rhyw, ac yn ôl oedran (oedran 0 i 15 wedi'u grwpio gyda'i gilydd, grwpiau oedran 10 oed hyd at 74 oed ac yna 75 oed a throsodd grwpio gyda'i gilydd). Mae'r amcangyfrifon fel yn y Diwrnod Cyfrifiad, 27 Mawrth 2011."
        }
      ]
    }
  }
}
```
