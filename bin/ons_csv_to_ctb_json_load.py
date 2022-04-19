"""Load metadata from CSV files and export in JSON format."""
import os
import logging
from functools import lru_cache
from ons_csv_to_ctb_json_bilingual import BilingualDict, Bilingual
from ons_csv_to_ctb_json_read import Reader, required, optional

PUBLIC_SECURITY_MNEMONIC = 'PUB'
GEOGRAPHIC_VARIABLE_TYPE = 'GEOG'


def isnumeric(string):
    """Check whether the string is numeric."""
    return string.isnumeric()


def isoneof(valid_values):
    """Return a function that checks whether the value is in the specified set of values."""
    valid_values_set = set(valid_values)

    def validate_fn(value):
        """Check if value is in set."""
        return value in valid_values_set

    return validate_fn


def append_to_list_in_dict(dictionary, key, value):
    """
    Append a value to the list at dictionary[key].

    An empty list is first created if the key is not in dictionary.
    """
    if key not in dictionary:
        dictionary[key] = []
    dictionary[key].append(value)


class Loader:
    """
    Loader contains methods for loading metadata objects from CSV files.

    Some of the CSV source files contain information on metadata objects. Basic validation is
    performed on each row e.g. to verify that required fields are populated,foreign keys are valid
    etc. The raw data is then modified and relationships to other objects are resolved to create
    a hierarchical representation of the metadata. Other files contain relationships between
    objects. The data in these files is also validated and relationships between objects are
    created.

    Many of the fields in this class are cached properties, with the data loaded on first access.
    """

    def __init__(self, input_directory):
        """Initialise MetadataLoader object."""
        self.input_directory = input_directory

    def read_file(self, filename, columns, unique_combo_fields=None):
        """
        Read data from a CSV file.

        A list of ons_csv_to_ctb_json_read.Row objects is returned. Each Row contains the data
        and corresponding line number.
        """
        full_filename = self.full_filename(filename)
        return Reader(full_filename, columns, unique_combo_fields).read()

    def full_filename(self, filename):
        """Add the input_directory path to the filename."""
        return os.path.join(self.input_directory, filename)

    @property
    @lru_cache(maxsize=1)
    def contacts(self):
        """Load contacts."""
        columns = [
            required('Contact_Id', unique=True),
            required('Contact_Name'),
            required('Contact_Email'),

            optional('Contact_Phone'),
            optional('Contact_Website'),
        ]
        contact_rows = self.read_file('Contact.csv', columns)

        contacts = {}
        for contact, _ in contact_rows:
            contacts[contact['Contact_Id']] = BilingualDict(contact)

        return contacts

    @property
    @lru_cache(maxsize=1)
    def sources(self):
        """Load sources."""
        columns = [
            required('Source_Mnemonic', unique=True),
            required('Source_Description'),
            required('Id'),

            optional('Source_Description_Welsh'),
            optional('Copyright_Statement'),
            optional('Licence'),
            optional('Nationals_Statistic_Certified'),
            optional('Methodology_Link'),
            optional('Methodology_Statement'),
            optional('Methodology_Statement_Welsh'),
            optional('SDC_Link'),
            optional('SDC_Statement'),
            optional('SDC_Statement_Welsh'),
            optional('Version'),
            optional('Contact_Id', validate_fn=isoneof(self.contacts.keys())),
        ]
        source_rows = self.read_file('Source.csv', columns)

        sources = {}
        for source, _ in source_rows:
            source['Source_Description'] = Bilingual(
                source.pop('Source_Description'),
                source.pop('Source_Description_Welsh'))
            source['Methodology_Statement'] = Bilingual(
                source.pop('Methodology_Statement'),
                source.pop('Methodology_Statement_Welsh'))
            source['SDC_Statement'] = Bilingual(
                source.pop('SDC_Statement'),
                source.pop('SDC_Statement_Welsh'))
            source['Contact'] = self.contacts.get(source.pop('Contact_Id'), None)

            del source['Id']

            sources[source['Source_Mnemonic']] = BilingualDict(source)

        return sources

    @property
    @lru_cache(maxsize=1)
    def census_releases(self):
        """Load census releases."""
        columns = [
            required('Census_Release_Number', unique=True),
            required('Census_Release_Description'),
            required('Release_Date'),
            required('Id'),
        ]
        census_release_rows = self.read_file('Census_Release.csv', columns)

        census_releases = {}
        for census_release, _ in census_release_rows:
            del census_release['Id']
            census_releases[census_release['Census_Release_Number']] = BilingualDict(
                census_release)

        return census_releases

    @property
    @lru_cache(maxsize=1)
    def security_classifications(self):
        """
        Load security classifications.

        Security classifications are not explicitly exported in the JSON output. Only datasets
        and classifications with a public security classification are exported.
        """
        filename = 'Security_Classification.csv'
        columns = [
            required('Security_Mnemonic', unique=True),
            required('Id'),

            optional('Security_Description_Welsh'),
            optional('Security_Description'),
        ]
        security_classification_rows = self.read_file(filename, columns)

        security_classifications = {sc.data['Security_Mnemonic'] for sc in
                                    security_classification_rows}

        # PUBLIC_SECURITY_MNEMONIC is used to identify datasets, variables and classifications that
        # should be included in the JSON output. Ensure that it is one of the Security_Mnemonic
        # values in the source file.
        if PUBLIC_SECURITY_MNEMONIC not in security_classifications:
            raise ValueError(f'{PUBLIC_SECURITY_MNEMONIC} not found as Security_Mnemonic for any '
                             f'entry in {self.full_filename(filename)}')

        return security_classifications

    @property
    @lru_cache(maxsize=1)
    def statistical_units(self):
        """Load statistical units."""
        columns = [
            required('Statistical_Unit', unique=True),
            required('Statistical_Unit_Description'),
            required('Id'),

            optional('Statistical_Unit_Description_Welsh'),
        ]
        statistical_unit_rows = self.read_file('Statistical_Unit.csv', columns)

        statistical_units = {}
        for stat_unit, _ in statistical_unit_rows:
            stat_unit['Statistical_Unit_Description'] = Bilingual(
                stat_unit.pop('Statistical_Unit_Description'),
                stat_unit.pop('Statistical_Unit_Description_Welsh'))

            del stat_unit['Id']

            statistical_units[stat_unit['Statistical_Unit']] = BilingualDict(stat_unit)

        return statistical_units

    @property
    @lru_cache(maxsize=1)
    def datasets(self):
        """Load datasets."""
        filename = 'Dataset.csv'
        geographic_variable_mnemonics = {k for k in self.variables if
                                         self.variables[k].private['Is_Geographic']}

        columns = [
            required('Dataset_Mnemonic', unique=True),
            required('Security_Mnemonic', validate_fn=isoneof(self.security_classifications)),
            required('Database_Mnemonic', validate_fn=isoneof(self.databases.keys())),
            required('Dataset_Title'),
            required('Id'),
            required('Geographic_Coverage'),
            required('Dataset_Population'),
            required('Statistical_Unit', validate_fn=isoneof(self.statistical_units.keys())),
            required('Version'),
            required('Dataset_Description'),

            optional('Dataset_Title_Welsh'),
            optional('Dataset_Description_Welsh'),
            optional('Dataset_Mnemonic_2011'),
            optional('Geographic_Coverage_Welsh'),
            optional('Dataset_Population_Welsh'),
            optional('Dissemination_Source'),
            optional('Release_Frequency'),
            optional('Last_Updated'),
            optional('Unique_Url'),
            optional('Signed_Off_Flag'),
            optional('Contact_Id', validate_fn=isoneof(self.contacts.keys())),
            optional('Geographic_Variable_Mnemonic',
                     validate_fn=isoneof(geographic_variable_mnemonics)),
        ]
        dataset_rows = self.read_file(filename, columns)

        dataset_mnemonics = [d.data['Dataset_Mnemonic'] for d in dataset_rows]

        dataset_to_related_datasets = self.load_dataset_to_related(dataset_mnemonics)
        dataset_to_keywords = self.load_dataset_to_keywords(dataset_mnemonics)
        dataset_to_publications = self.load_dataset_to_publications(dataset_mnemonics)
        dataset_to_releases = self.load_dataset_to_releases(dataset_mnemonics)
        dataset_to_classifications = self.load_dataset_to_classifications(dataset_mnemonics)

        datasets = {}
        for dataset, line_num in dataset_rows:
            dataset_mnemonic = dataset.pop('Dataset_Mnemonic')
            database_mnemonic = dataset.pop('Database_Mnemonic')

            dataset['Geographic_Coverage'] = Bilingual(dataset.pop('Geographic_Coverage'),
                                                       dataset.pop('Geographic_Coverage_Welsh'))
            dataset['Dataset_Population'] = Bilingual(dataset.pop('Dataset_Population'),
                                                      dataset.pop('Dataset_Population_Welsh'))
            dataset['Statistical_Unit'] = self.statistical_units.get(
                dataset.pop('Statistical_Unit'), None)
            dataset['Contact'] = self.contacts.get(dataset.pop('Contact_Id'), None)

            dataset['Keywords'] = dataset_to_keywords.get(dataset_mnemonic, [])
            dataset['Related_Datasets'] = dataset_to_related_datasets.get(dataset_mnemonic, [])
            dataset['Census_Releases'] = dataset_to_releases.get(dataset_mnemonic, [])
            dataset['Publications'] = dataset_to_publications.get(dataset_mnemonic, [])
            dataset_classifications = dataset_to_classifications.get(dataset_mnemonic, [])

            if dataset['Geographic_Variable_Mnemonic']:
                dataset_classifications = [
                    dataset['Geographic_Variable_Mnemonic'], *dataset_classifications]

            # If the dataset is public then ensure that there is at least one classification and
            # that all the classifications are also public.
            if dataset['Security_Mnemonic'] == PUBLIC_SECURITY_MNEMONIC:
                if not dataset_classifications:
                    raise ValueError(
                        f'Reading {self.full_filename(filename)}:{line_num} {dataset_mnemonic} '
                        'has no associated classifications or geographic variable')

                for classification in dataset_classifications:
                    if self.classifications[classification].private['Security_Mnemonic'] != \
                            PUBLIC_SECURITY_MNEMONIC:
                        raise ValueError(
                            f'Reading {self.full_filename(filename)}:{line_num} Public ONS '
                            f'dataset {dataset_mnemonic} has non-public classification '
                            f'{classification}')
                    if classification not in self.database_to_classifications.get(
                            database_mnemonic, []):
                        raise ValueError(
                            f'Reading {self.full_filename(filename)}:{line_num} '
                            f'{dataset_mnemonic} has classification {classification} '
                            f'that is not in database {database_mnemonic}')

            del dataset['Id']
            del dataset['Signed_Off_Flag']

            datasets[dataset_mnemonic] = BilingualDict(
                dataset,
                # The private fields and not included in the English/Welsh variants of datasets.
                # They are used later in processing and included in different parts of the metadata
                # hierarchy.
                private={
                    'Security_Mnemonic': dataset.pop('Security_Mnemonic'),
                    'Dataset_Title': Bilingual(dataset.pop('Dataset_Title'),
                                               dataset.pop('Dataset_Title_Welsh')),
                    'Dataset_Description': Bilingual(dataset.pop('Dataset_Description'),
                                                     dataset.pop('Dataset_Description_Welsh')),
                    'Database_Mnemonic': database_mnemonic,
                    'Classifications': dataset_classifications,
                })

        return datasets

    @property
    @lru_cache(maxsize=1)
    def databases(self):
        """Load databases."""
        columns = [
            required('Database_Mnemonic', unique=True),
            required('Source_Mnemonic', validate_fn=isoneof(self.sources.keys())),
            required('Database_Title'),
            required('Id'),
            required('Database_Description'),
            required('Version'),

            optional('Database_Title_Welsh'),
            optional('Database_Description_Welsh'),
            optional('Cantabular_DB_Flag'),
            optional('IAR_Asset_Id'),
        ]
        database_rows = self.read_file('Database.csv', columns)

        databases = {}
        for database, _ in database_rows:
            database['Database_Description'] = Bilingual(
                database.pop('Database_Description'),
                database.pop('Database_Description_Welsh'))
            database['Source'] = self.sources.get(database.pop('Source_Mnemonic'), None)

            del database['Id']
            del database['IAR_Asset_Id']

            database_mnemonic = database.pop('Database_Mnemonic')
            databases[database_mnemonic] = BilingualDict(
                database,
                # Database_Title is used to populate a Cantabular built-in field.
                private={'Database_Title': Bilingual(database.pop('Database_Title'),
                                                     database.pop('Database_Title_Welsh'))})

        return databases

    @property
    @lru_cache(maxsize=1)
    def categories(self):
        """
        Load categories.

        Cantabular has a built-in catLabels concept. This is a dictionary of category codes to
        category labels. The data from the categories file are converted to this format.

        English values are excluded. These will be present in the codebook. Unpopulated Welsh
        values are also excluded.
        """
        filename = 'Category.csv'
        columns = [
            required('Category_Code'),
            required('Classification_Mnemonic', validate_fn=isoneof(self.classifications.keys())),
            required('Label'),
            required('Id'),
            # Source_Variable_Mnemonic values are not validated as they are not required by
            # metadata server.
            required('Source_Variable_Mnemonic'),
            required('Version'),

            # Sort_Order values are not validated as this is an optional field.
            optional('Sort_Order'),
            optional('Label_Welsh'),
            optional('Target_Variable_Mnemonic'),
        ]
        category_rows = self.read_file(
            filename, columns,
            # There can only be one row for each Category_Code/Classification_Mnemonic combination.
            unique_combo_fields=['Category_Code', 'Classification_Mnemonic'])

        classification_to_cats = {}
        for cat, _ in category_rows:
            append_to_list_in_dict(classification_to_cats, cat['Classification_Mnemonic'], cat)

        categories = {}
        for classification_mnemonic, one_var_categories in classification_to_cats.items():
            num_cat_items = \
                self.classifications[classification_mnemonic].private['Number_Of_Category_Items']
            if len(one_var_categories) != num_cat_items:
                raise ValueError(f'Reading {self.full_filename(filename)} '
                                 f'Unexpected number of categories for {classification_mnemonic}: '
                                 f'expected {num_cat_items} but found {len(one_var_categories)}')

            welsh_cats = {cat['Category_Code']: cat['Label_Welsh'] for cat in one_var_categories
                          if cat['Label_Welsh']}
            if welsh_cats:
                categories[classification_mnemonic] = Bilingual(None, welsh_cats)

        return categories

    @property
    @lru_cache(maxsize=1)
    def topics(self):
        """Load topics."""
        columns = [
            required('Topic_Mnemonic', unique=True),
            required('Topic_Title'),
            required('Topic_Description'),
            required('Id'),

            optional('Topic_Description_Welsh'),
            optional('Topic_Title_Welsh'),
        ]
        topic_rows = self.read_file('Topic.csv', columns)

        topics = {}
        for topic, _ in topic_rows:
            topic['Topic_Description'] = Bilingual(topic.pop('Topic_Description'),
                                                   topic.pop('Topic_Description_Welsh'))
            topic['Topic_Title'] = Bilingual(topic.pop('Topic_Title'),
                                             topic.pop('Topic_Title_Welsh'))

            del topic['Id']
            topics[topic['Topic_Mnemonic']] = BilingualDict(topic)

        return topics

    @property
    @lru_cache(maxsize=1)
    def questions(self):
        """Load questions."""
        columns = [
            required('Question_Code', unique=True),
            required('Question_Label'),
            required('Version'),
            required('Id'),

            optional('Question_Label_Welsh'),
            optional('Reason_For_Asking_Question'),
            optional('Reason_For_Asking_Question_Welsh'),
            optional('Question_First_Asked_In_Year'),
        ]
        question_rows = self.read_file('Question.csv', columns)

        questions = {}
        for question, _ in question_rows:
            question['Question_Label'] = Bilingual(
                question.pop('Question_Label'),
                question.pop('Question_Label_Welsh'))
            question['Reason_For_Asking_Question'] = Bilingual(
                question.pop('Reason_For_Asking_Question'),
                question.pop('Reason_For_Asking_Question_Welsh'))
            del question['Id']
            questions[question['Question_Code']] = BilingualDict(question)

        return questions

    @property
    @lru_cache(maxsize=1)
    def variable_types(self):
        """Load variable types."""
        filename = 'Variable_Type.csv'
        columns = [
            required('Variable_Type_Code', unique=True),
            required('Variable_Type_Description'),
            required('Id'),

            optional('Variable_Type_Description_Welsh'),
        ]
        variable_type_rows = self.read_file(filename, columns)

        variable_types = {}
        for var_type, _ in variable_type_rows:
            var_type['Variable_Type_Description'] = Bilingual(
                var_type.pop('Variable_Type_Description'),
                var_type.pop('Variable_Type_Description_Welsh'))
            del var_type['Id']

            variable_types[var_type['Variable_Type_Code']] = BilingualDict(var_type)

        # GEOGRAPHIC_VARIABLE_TYPE is used to identify geographic variables. Ensure that it is
        # one of the Variable_Type_Code values in the source file.
        if GEOGRAPHIC_VARIABLE_TYPE not in variable_types:
            raise ValueError(f'{GEOGRAPHIC_VARIABLE_TYPE} not found as Variable_Type_Code for any '
                             f'entry in {self.full_filename(filename)}')

        return variable_types

    @property
    @lru_cache(maxsize=1)
    def variables(self):
        """Load variables."""
        filename = 'Variable.csv'
        columns = [
            required('Variable_Mnemonic', unique=True),
            required('Security_Mnemonic', validate_fn=isoneof(self.security_classifications)),
            required('Variable_Type_Code', validate_fn=isoneof(self.variable_types.keys())),
            required('Variable_Title'),
            required('Variable_Description'),
            optional('Statistical_Unit', validate_fn=isoneof(self.statistical_units.keys())),
            required('Id'),
            required('Version'),

            optional('Variable_Title_Welsh'),
            optional('Variable_Description_Welsh'),
            optional('Variable_Mnemonic_2011'),
            optional('Comparability_Comments'),
            optional('Comparability_Comments_Welsh'),
            optional('Uk_Comparison_Comments'),
            optional('Uk_Comparison_Comments_Welsh'),
            optional('Geographic_Abbreviation'),
            optional('Geographic_Abbreviation_Welsh'),
            optional('Geographic_Theme'),
            optional('Geographic_Theme_Welsh'),
            optional('Geographic_Coverage'),
            optional('Geographic_Coverage_Welsh'),
            optional('Topic_Mnemonic', validate_fn=isoneof(self.topics.keys())),
            optional('Signed_Off_Flag'),
            optional('Number_Of_Classifications'),
        ]
        variable_rows = self.read_file(filename, columns)

        variable_mnemonics = [v.data['Variable_Mnemonic'] for v in variable_rows]
        variable_to_keywords = self.load_variable_to_keywords(variable_mnemonics)
        variable_to_source_questions = self.load_variable_to_questions(variable_mnemonics)

        geo_fields = {'Geographic_Abbreviation', 'Geographic_Abbreviation_Welsh',
                      'Geographic_Theme', 'Geographic_Theme_Welsh', 'Geographic_Coverage',
                      'Geographic_Coverage_Welsh'}
        variables = {}
        for variable, line_num in variable_rows:
            # Ensure that non-geographic variables do not have geographic values set.
            is_geographic = variable['Variable_Type_Code'] == GEOGRAPHIC_VARIABLE_TYPE
            if not is_geographic:
                for geo_field in geo_fields:
                    if variable[geo_field]:
                        raise ValueError(f'Reading {self.full_filename(filename)}:{line_num} '
                                         f'{geo_field} specified for non geographic variable: '
                                         f'{variable["Variable_Mnemonic"]}')
            variable_title = Bilingual(
                variable.pop('Variable_Title'),
                variable.pop('Variable_Title_Welsh'))

            variable['Variable_Title'] = variable_title
            variable['Variable_Description'] = Bilingual(
                variable.pop('Variable_Description'),
                variable.pop('Variable_Description_Welsh'))
            variable['Comparability_Comments'] = Bilingual(
                variable.pop('Comparability_Comments'),
                variable.pop('Comparability_Comments_Welsh'))
            variable['Uk_Comparison_Comments'] = Bilingual(
                variable.pop('Uk_Comparison_Comments'),
                variable.pop('Uk_Comparison_Comments_Welsh'))
            variable['Geographic_Abbreviation'] = Bilingual(
                variable.pop('Geographic_Abbreviation'),
                variable.pop('Geographic_Abbreviation_Welsh'))
            variable['Geographic_Theme'] = Bilingual(
                variable.pop('Geographic_Theme'),
                variable.pop('Geographic_Theme_Welsh'))
            variable['Geographic_Coverage'] = Bilingual(
                variable.pop('Geographic_Coverage'),
                variable.pop('Geographic_Coverage_Welsh'))

            variable['Variable_Type'] = self.variable_types.get(variable.pop('Variable_Type_Code'),
                                                                None)
            variable['Statistical_Unit'] = self.statistical_units.get(
                variable.pop('Statistical_Unit'), None)
            variable['Topic'] = self.topics.get(variable.pop('Topic_Mnemonic'), None)

            variable['Keywords'] = variable_to_keywords.get(variable['Variable_Mnemonic'], [])
            variable['Questions'] = variable_to_source_questions.get(
                variable['Variable_Mnemonic'], [])

            del variable['Id']
            del variable['Signed_Off_Flag']
            # Number_Of_Classifications is not validated
            del variable['Number_Of_Classifications']

            variables[variable['Variable_Mnemonic']] = BilingualDict(
                variable,
                # A check is performed elsewhere to ensure that public classifications have public
                # variables. Is_Geographic is used to check whether variables are geographic.
                # Variable_Title and Version are used when creating classifications for geographic
                # variables.
                private={'Security_Mnemonic': variable.pop('Security_Mnemonic'),
                         'Is_Geographic': is_geographic,
                         'Variable_Title': variable_title,
                         'Version': variable['Version']})
        return variables

    @property
    @lru_cache(maxsize=1)
    def classifications(self):
        """Load classifications."""
        filename = 'Classification.csv'
        columns = [
            required('Id'),
            required('Classification_Mnemonic', unique=True),
            required('Number_Of_Category_Items', validate_fn=isnumeric),
            required('Variable_Mnemonic', validate_fn=isoneof(self.variables.keys())),
            required('Classification_Label'),
            required('Security_Mnemonic', validate_fn=isoneof(self.security_classifications)),
            required('Version'),

            optional('Classification_Label_Welsh'),
            optional('Mnemonic_2011'),
            optional('Parent_Classification_Mnemonic'),
            optional('Default_Classification_Flag'),
            optional('Signed_Off_Flag'),
            optional('Flat_Classification_Flag'),
        ]
        classification_rows = self.read_file(filename, columns)

        classification_mnemonics = [c.data['Classification_Mnemonic'] for c in classification_rows]
        classification_to_topics = self.load_classification_to_topics(classification_mnemonics)

        classifications = {}
        for classification, line_num in classification_rows:
            variable_mnemonic = classification.pop('Variable_Mnemonic')
            classification_mnemonic = classification.pop('Classification_Mnemonic')
            classification['ONS_Variable'] = self.variables[variable_mnemonic]
            classification['Topics'] = classification_to_topics.get(classification_mnemonic, [])

            # Ensure that if a classification is public that the associated variable is public.
            if classification['Security_Mnemonic'] == PUBLIC_SECURITY_MNEMONIC:
                variable = classification['ONS_Variable']
                if variable.private['Security_Mnemonic'] != PUBLIC_SECURITY_MNEMONIC:
                    raise ValueError(f'Reading {self.full_filename(filename)}:{line_num} '
                                     f'Public classification {classification_mnemonic} has '
                                     f'non-public variable {variable_mnemonic}')

            del classification['Signed_Off_Flag']
            del classification['Flat_Classification_Flag']
            del classification['Id']

            num_cat_items = classification.pop('Number_Of_Category_Items')
            if not num_cat_items:
                num_cat_items = 0
            else:
                num_cat_items = int(num_cat_items)

            classifications[classification_mnemonic] = BilingualDict(
                classification,
                # The private fields and not included in the English/Welsh variants of datasets.
                # They are used later in processing and included in different parts of the metadata
                # hierarchy.
                private={
                    'Number_Of_Category_Items': num_cat_items,
                    'Security_Mnemonic': classification.pop('Security_Mnemonic'),
                    'Classification_Label': Bilingual(
                        classification.pop('Classification_Label'),
                        classification.pop('Classification_Label_Welsh')),
                    'Variable_Mnemonic': variable_mnemonic})

        # Every geographic variable must have a corresponding classification with the same
        # mnemonic. This is due to the fact that the dataset specifies a geographic variable
        # rather than a classification. Automatically create an entry if it does not already
        # exist.
        for variable_mnemonic, variable in self.variables.items():
            if variable.private['Is_Geographic'] and variable_mnemonic not in classifications:
                logging.debug('Creating classification for geographic variable: '
                              f'{variable_mnemonic}')
                classifications[variable_mnemonic] = BilingualDict(
                    {
                        'Mnemonic_2011': None,
                        'Parent_Classification_Mnemonic': variable_mnemonic,
                        'Default_Classification_Flag': None,
                        'Version': variable.private['Version'],
                        'ONS_Variable': variable,
                        'Topics': [],
                    },
                    private={
                        'Number_Of_Category_Items': 0,
                        'Security_Mnemonic': variable.private['Security_Mnemonic'],
                        'Classification_Label': variable.private['Variable_Title'],
                        'Variable_Mnemonic': variable_mnemonic})

        return classifications

    @property
    @lru_cache(maxsize=1)
    def database_to_classifications(self):
        """
        Load the classifications associated with each database.

        This involves reading the Database_Variable.csv file which identifies the variables
        associated with each database, and then identifying the classifications associated with
        each variable.
        """
        columns = [
            required('Variable_Mnemonic', validate_fn=isoneof(self.variables.keys())),
            required('Database_Mnemonic', validate_fn=isoneof(self.databases.keys())),
            required('Id'),
            required('Version'),
        ]
        database_variable_rows = self.read_file(
            'Database_Variable.csv', columns,
            # There can only be one row for each Variable_Mnemonic/Database_Mnemonic combination.
            unique_combo_fields=['Variable_Mnemonic', 'Database_Mnemonic'])

        db_to_var_mnemonics = {}
        for db_var, _ in database_variable_rows:
            append_to_list_in_dict(db_to_var_mnemonics, db_var['Database_Mnemonic'],
                                   db_var['Variable_Mnemonic'])

        database_to_classifications = {}
        for database_mnemonic, db_vars in db_to_var_mnemonics.items():
            database_to_classifications[database_mnemonic] = [
                k for k, v in self.classifications.items() if
                v.private['Variable_Mnemonic'] in db_vars]

        return database_to_classifications

    def load_dataset_to_related(self, dataset_mnemonics):
        """Load the related datasets relationships."""
        filename = 'Related_Datasets.csv'
        columns = [
            required('Related_Dataset_Mnemonic', validate_fn=isoneof(dataset_mnemonics)),
            required('Dataset_Mnemonic', validate_fn=isoneof(dataset_mnemonics)),
            required('Id'),
        ]
        related_dataset_rows = self.read_file(
            filename, columns,
            # There can only be one row for each Related_Dataset_Mnemonic/Dataset_Mnemonic
            # combination.
            unique_combo_fields=['Related_Dataset_Mnemonic', 'Dataset_Mnemonic'])

        ds_to_related_ds_mnemonics = {}
        for rel_ds, line_num in related_dataset_rows:
            if rel_ds['Dataset_Mnemonic'] == rel_ds['Related_Dataset_Mnemonic']:
                raise ValueError(f'Reading {self.full_filename(filename)}:{line_num}'
                                 ' Dataset_Mnemonic is the same as Related_Dataset_Mnemonic: '
                                 f'{rel_ds["Dataset_Mnemonic"]}')

            append_to_list_in_dict(ds_to_related_ds_mnemonics, rel_ds['Dataset_Mnemonic'],
                                   rel_ds['Related_Dataset_Mnemonic'])

        return ds_to_related_ds_mnemonics

    def load_dataset_to_keywords(self, dataset_mnemonics):
        """Load keywords associated with each dataset."""
        columns = [
            required('Dataset_Keyword'),
            required('Dataset_Mnemonic', validate_fn=isoneof(dataset_mnemonics)),
            required('Id'),

            optional('Dataset_Keyword_Welsh'),
        ]
        dataset_keyword_rows = self.read_file(
            'Dataset_Keyword.csv', columns,
            # There can only be one row for each Dataset_Mnemonic/Dataset_Keyword combination.
            unique_combo_fields=['Dataset_Mnemonic', 'Dataset_Keyword'])

        dataset_to_keywords = {}
        for ds_key, _ in dataset_keyword_rows:
            append_to_list_in_dict(dataset_to_keywords, ds_key['Dataset_Mnemonic'],
                                   Bilingual(ds_key['Dataset_Keyword'],
                                             ds_key['Dataset_Keyword_Welsh']))

        return dataset_to_keywords

    def load_dataset_to_publications(self, dataset_mnemonics):
        """Load publications associated with each dataset."""
        columns = [
            required('Publication_Mnemonic', unique=True),
            required('Dataset_Mnemonic', validate_fn=isoneof(dataset_mnemonics)),
            required('Id'),

            optional('Publication_Title'),
            optional('Publisher_Name'),
            optional('Publisher_Website'),
        ]
        publication_dataset_rows = self.read_file('Publication_Dataset.csv', columns)

        dataset_to_pubs = {}
        for ds_pub, _ in publication_dataset_rows:
            del ds_pub['Id']
            append_to_list_in_dict(dataset_to_pubs, ds_pub.pop('Dataset_Mnemonic'),
                                   BilingualDict(ds_pub))

        return dataset_to_pubs

    def load_dataset_to_releases(self, dataset_mnemonics):
        """Load releases associated with each dataset."""
        columns = [
            required('Census_Release_Number', validate_fn=isoneof(self.census_releases.keys())),
            required('Dataset_Mnemonic', validate_fn=isoneof(dataset_mnemonics)),
            required('Id'),
        ]
        release_dataset_rows = self.read_file(
            'Release_Dataset.csv', columns,
            # There can only be one row for each Dataset_Mnemonic/Census_Release_Number
            # combination.
            unique_combo_fields=['Dataset_Mnemonic', 'Census_Release_Number'])

        dataset_to_releases = {}
        for rel_ds, _ in release_dataset_rows:
            append_to_list_in_dict(dataset_to_releases, rel_ds['Dataset_Mnemonic'],
                                   self.census_releases[rel_ds['Census_Release_Number']])

        return dataset_to_releases

    def load_variable_to_keywords(self, variable_mnemonics):
        """Load keywords associated with each variable."""
        columns = [
            required('Variable_Mnemonic', validate_fn=isoneof(variable_mnemonics)),
            required('Variable_Keyword'),
            required('Id'),

            optional('Variable_Keyword_Welsh'),
        ]
        variable_keyword_rows = self.read_file(
            'Variable_Keyword.csv', columns,
            # There can only be one row for each Variable_Mnemonic/Variable_Keyword combination.
            unique_combo_fields=['Variable_Mnemonic', 'Variable_Keyword'])

        variable_to_keywords = {}
        for var_key, _ in variable_keyword_rows:
            append_to_list_in_dict(variable_to_keywords, var_key['Variable_Mnemonic'],
                                   Bilingual(var_key['Variable_Keyword'],
                                             var_key['Variable_Keyword_Welsh']))

        return variable_to_keywords

    def load_variable_to_questions(self, variable_mnemonics):
        """Load questions associated with each variable."""
        columns = [
            required('Source_Question_Code', validate_fn=isoneof(self.questions.keys())),
            required('Variable_Mnemonic', validate_fn=isoneof(variable_mnemonics)),
            required('Id'),
        ]
        variable_source_question_rows = self.read_file(
            'Variable_Source_Question.csv', columns,
            # There can only be one row for each Variable_Mnemonic/Source_Question_Code
            # combination.
            unique_combo_fields=['Variable_Mnemonic', 'Source_Question_Code'])

        var_to_src_questions = {}
        for src_q, _ in variable_source_question_rows:
            append_to_list_in_dict(var_to_src_questions, src_q['Variable_Mnemonic'],
                                   self.questions[src_q['Source_Question_Code']])

        return var_to_src_questions

    def load_dataset_to_classifications(self, dataset_mnemonics):
        """
        Load classifications associated with each dataset.

        Each classification associated with a dataset has a Processing_Priority. These priorities
        indicate the order of the classifications. The priorities for each dataset must be unique
        and sequential, starting from 1. The classifications are ordered based on the priorities.
        """
        filename = 'Dataset_Classification.csv'
        columns = [
            required('Classification_Mnemonic', validate_fn=isoneof(self.classifications.keys())),
            required('Dataset_Mnemonic', validate_fn=isoneof(dataset_mnemonics)),
            required('Processing_Priority', validate_fn=isnumeric),
            required('Id'),
            required('Version'),
        ]
        dataset_classification_rows = self.read_file(
            filename, columns,
            # There can only be one row for each Dataset_Mnemonic/Classification_Mnemonic
            # combination.
            unique_combo_fields=['Dataset_Mnemonic', 'Classification_Mnemonic'])

        ds_to_classifications = {}
        for ds_class, _ in dataset_classification_rows:
            append_to_list_in_dict(ds_to_classifications, ds_class['Dataset_Mnemonic'], ds_class)

        ds_to_classification_mnemonics = {}
        for dataset_mnemonic, classifications_for_dataset in ds_to_classifications.items():
            processing_priorities = [int(c['Processing_Priority']) for c in
                                     classifications_for_dataset]
            if set(processing_priorities) != set(range(1, len(processing_priorities) + 1)):
                raise ValueError(f'Reading {self.full_filename(filename)} '
                                 f'Invalid processing_priorities {processing_priorities} '
                                 f'for dataset {dataset_mnemonic}')
            ds_to_classification_mnemonics[dataset_mnemonic] = [None] * len(processing_priorities)
            for i, priority in enumerate(processing_priorities):
                ds_to_classification_mnemonics[dataset_mnemonic][priority - 1] = \
                    classifications_for_dataset[i]['Classification_Mnemonic']

        return ds_to_classification_mnemonics

    def load_classification_to_topics(self, classification_mnemonics):
        """Load topics associated with each classification."""
        columns = [
            required('Topic_Mnemonic', validate_fn=isoneof(self.topics.keys())),
            required('Classification_Mnemonic', validate_fn=isoneof(classification_mnemonics)),
            required('Id'),
        ]
        topic_classification_rows = self.read_file(
            'Topic_Classification.csv', columns,
            # There can only be one row for each Classification_Mnemonic/Topic_Mnemonic
            # combination.
            unique_combo_fields=['Classification_Mnemonic', 'Topic_Mnemonic'])

        classification_to_topics = {}
        for topic_class, _ in topic_classification_rows:
            append_to_list_in_dict(classification_to_topics,
                                   topic_class['Classification_Mnemonic'],
                                   self.topics[topic_class['Topic_Mnemonic']])

        return classification_to_topics
