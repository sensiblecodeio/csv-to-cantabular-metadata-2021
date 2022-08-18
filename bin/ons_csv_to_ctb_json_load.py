"""Load metadata from CSV files and export in JSON format."""
import os
import logging
from collections import namedtuple
from functools import lru_cache
from ons_csv_to_ctb_json_bilingual import BilingualDict, Bilingual
from ons_csv_to_ctb_json_read import Reader, required, optional
from ons_csv_to_ctb_json_geo import read_geo_cats
from ons_csv_to_ctb_json_ds_vars import DatasetVarsBuilder, DatasetVariables

PUBLIC_SECURITY_MNEMONIC = 'PUB'
GEOGRAPHIC_VARIABLE_TYPE = 'GEOG'
TABULAR_DATABASE_TYPE = 'AGGDATA'

DatabaseClassifications = namedtuple('DatabaseClassifications',
                                     'classifications lowest_geog_variable')


def isnumeric(string):
    """Check whether the string is numeric."""
    return string.isnumeric()


def is_y_or_n(string):
    """Return true if the string is either 'Y' or 'N'."""
    return string in ['Y', 'N']


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

    def __init__(self, input_directory, geography_file, best_effort=False, dataset_filter=''):
        """Initialise MetadataLoader object."""
        self.input_directory = input_directory
        self.geography_file = geography_file
        self.dataset_filter = dataset_filter
        self._error_count = 0

        def raise_value_error(msg):
            """Raise a ValueError exception."""
            raise ValueError(msg)

        def log_error(msg):
            """Log the error."""
            self._error_count += 1
            logging.warning(msg)

        self.recoverable_error = log_error if best_effort else raise_value_error

    def error_count(self):
        """Return number of errors."""
        return self._error_count

    def read_file(self, filename, columns, unique_combo_fields=None):
        """
        Read data from a CSV file.

        A list of ons_csv_to_ctb_json_read.Row objects is returned. Each Row contains the data
        and corresponding line number.
        """
        full_filename = self.full_filename(filename)
        return Reader(full_filename, columns, self.recoverable_error, unique_combo_fields,
                      self.dataset_filter).read()

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
            required('Version'),

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
            required('Security_Description'),

            optional('Security_Description_Welsh'),
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
        columns = [
            required('Dataset_Mnemonic', unique=True),
            required('Security_Mnemonic', validate_fn=isoneof(self.security_classifications)),
            required('Source_Database_Mnemonic', validate_fn=isoneof(self.databases.keys())),
            required('Dataset_Title'),
            required('Id'),
            required('Geographic_Coverage'),
            required('Dataset_Population'),
            required('Statistical_Unit', validate_fn=isoneof(self.statistical_units.keys())),
            required('Version'),
            required('Dataset_Description'),
            required('Signed_Off_Flag', validate_fn=is_y_or_n),

            optional('Dataset_Title_Welsh'),
            optional('Dataset_Description_Welsh'),
            optional('Dataset_Mnemonic_2011'),
            optional('Geographic_Coverage_Welsh'),
            optional('Dataset_Population_Welsh'),
            optional('Last_Updated'),
            optional('Contact_Id', validate_fn=isoneof(self.contacts.keys())),
            optional('Observation_Type_Code', validate_fn=isoneof(self.observation_types.keys())),
            optional('Pre_Built_Database_Mnemonic', validate_fn=isoneof(self.databases.keys())),
        ]
        dataset_rows = self.read_file(filename, columns)

        dataset_mnemonics = [d.data['Dataset_Mnemonic'] for d in dataset_rows]

        dataset_to_related_datasets = self.load_dataset_to_related(dataset_mnemonics)
        dataset_to_publications = self.load_dataset_to_publications(dataset_mnemonics)
        dataset_to_releases = self.load_dataset_to_releases(dataset_mnemonics)
        dataset_to_variables = self.load_dataset_to_variables(dataset_mnemonics)

        # All datasets in a database must have the same observation type
        database_observation_type = dict()
        datasets = {}
        for dataset, row_num in dataset_rows:
            drop_dataset = False
            dataset_mnemonic = dataset.pop('Dataset_Mnemonic')
            source_database_mnemonic = dataset.pop('Source_Database_Mnemonic')
            if self.databases[source_database_mnemonic].private['Database_Type_Code'] == \
                    TABULAR_DATABASE_TYPE:
                self.recoverable_error(
                    f'Reading {self.full_filename(filename)}:{row_num} {dataset_mnemonic} '
                    f'has Source_Database_Mnemonic {source_database_mnemonic} which has invalid '
                    f'Database_Type_Code: {TABULAR_DATABASE_TYPE}')
                # The dataset should probably be dropped here but there are some ongoing
                # discussions around database types.
                # drop_dataset = True

            pre_built_database_mnemonic = dataset.pop('Pre_Built_Database_Mnemonic')
            if pre_built_database_mnemonic and \
                    self.databases[pre_built_database_mnemonic].private['Database_Type_Code'] != \
                    TABULAR_DATABASE_TYPE:
                self.recoverable_error(
                    f'Reading {self.full_filename(filename)}:{row_num} {dataset_mnemonic} '
                    f'has Pre_Built_Database_Mnemonic {pre_built_database_mnemonic} which has '
                    f'invalid Database_Type_Code: '
                    f'{self.databases[pre_built_database_mnemonic].private["Database_Type_Code"]}')
                drop_dataset = True

            database_mnemonic = pre_built_database_mnemonic \
                if pre_built_database_mnemonic else source_database_mnemonic

            dataset['Geographic_Coverage'] = Bilingual(dataset.pop('Geographic_Coverage'),
                                                       dataset.pop('Geographic_Coverage_Welsh'))
            dataset['Dataset_Population'] = Bilingual(dataset.pop('Dataset_Population'),
                                                      dataset.pop('Dataset_Population_Welsh'))
            dataset['Statistical_Unit'] = self.statistical_units.get(
                dataset.pop('Statistical_Unit'), None)
            dataset['Contact'] = self.contacts.get(dataset.pop('Contact_Id'), None)
            observation_type_code = dataset.pop('Observation_Type_Code')
            dataset['Observation_Type'] = self.observation_types.get(observation_type_code, None)

            if database_mnemonic not in database_observation_type:
                database_observation_type[database_mnemonic] = observation_type_code
            elif database_observation_type[database_mnemonic] != observation_type_code:
                self.recoverable_error(
                    f'Reading {self.full_filename(filename)}:{row_num} {dataset_mnemonic} '
                    f'has different observation type {observation_type_code} from other '
                    f'datasets in database {database_mnemonic}: '
                    f'{database_observation_type[database_mnemonic]}')
                # The dataset should probably be dropped here but the data isn't yet 100% correct
                # drop_dataset = True

            dataset['Related_Datasets'] = dataset_to_related_datasets.get(dataset_mnemonic, [])
            dataset['Census_Releases'] = dataset_to_releases.get(dataset_mnemonic, [])
            dataset['Publications'] = dataset_to_publications.get(dataset_mnemonic, [])
            dataset_variables = dataset_to_variables.get(
                dataset_mnemonic, DatasetVariables([], []))

            alternate_geog_variables = (dataset_variables.alternate_geog_variables if
                                        dataset_variables.alternate_geog_variables else [])
            dataset['Alternate_Geographic_Variables'] = alternate_geog_variables
            all_classifications = dataset_variables.classifications + alternate_geog_variables

            # If the dataset is public then ensure that there is at least one classification and
            # that all the classifications are also public.
            if dataset['Security_Mnemonic'] == PUBLIC_SECURITY_MNEMONIC:
                if not dataset_variables.classifications:
                    self.recoverable_error(
                        f'Reading {self.full_filename(filename)}:{row_num} {dataset_mnemonic} '
                        'has no associated classifications or geographic variable')
                    drop_dataset = True

                for classification in all_classifications:
                    if self.classifications[classification].private['Security_Mnemonic'] != \
                            PUBLIC_SECURITY_MNEMONIC:
                        self.recoverable_error(
                            f'Reading {self.full_filename(filename)}:{row_num} Public ONS '
                            f'dataset {dataset_mnemonic} has non-public classification '
                            f'{classification}')
                        drop_dataset = True

                    if classification not in \
                            self.databases[source_database_mnemonic].private['Classifications']:
                        self.recoverable_error(
                            f'Reading {self.full_filename(filename)}:{row_num} '
                            f'{dataset_mnemonic} has classification {classification} '
                            f'that is not in source database {source_database_mnemonic}')
                        # Do not set drop_dataset to True.
                        # Keeping the dataset in this scenario produces more useful data
                        # when operating in best effort mode.

                    if pre_built_database_mnemonic and classification not in \
                            self.databases[pre_built_database_mnemonic].private['Classifications']:
                        self.recoverable_error(
                            f'Reading {self.full_filename(filename)}:{row_num} '
                            f'{dataset_mnemonic} has classification {classification} '
                            f'that is not in pre built database {pre_built_database_mnemonic}')
                        # Do not set drop_dataset to True.
                        # Keeping the dataset in this scenario produces more useful data
                        # when operating in best effort mode.

            if drop_dataset:
                logging.warning(
                    f'Reading {self.full_filename(filename)}:{row_num} dropping record')
                continue

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
                    'Codebook_Mnemonics': [self.classifications[c].private['Codebook_Mnemonic'] for
                                           c in dataset_variables.classifications],
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
            # This should be mandatory but is not yet populated
            optional('Cantabular_DB_Flag', validate_fn=is_y_or_n),
            required('Database_Type_Code', validate_fn=isoneof(self.database_types.keys())),

            optional('Database_Title_Welsh'),
            optional('Database_Description_Welsh'),
            optional('IAR_Asset_Id'),
        ]
        database_rows = self.read_file('Database.csv', columns)

        database_mnemonics = [d.data['Database_Mnemonic'] for d in database_rows]
        database_to_classifications = self.load_database_to_classifications(database_mnemonics)

        databases = {}
        for database, _ in database_rows:
            database['Source'] = self.sources.get(database.pop('Source_Mnemonic'), None)

            del database['Id']
            del database['IAR_Asset_Id']

            database_mnemonic = database.pop('Database_Mnemonic')

            db_classifications = database_to_classifications.get(database_mnemonic,
                                                                 DatabaseClassifications([], None))
            database['Lowest_Geog_Variable'] = db_classifications.lowest_geog_variable

            database_type_code = database.pop('Database_Type_Code')
            database['Database_Type'] = self.database_types.get(database_type_code, None)

            databases[database_mnemonic] = BilingualDict(
                database,
                # Database_Title is used to populate a Cantabular built-in field.
                private={'Database_Title': Bilingual(database.pop('Database_Title'),
                                                     database.pop('Database_Title_Welsh')),
                         'Database_Description': Bilingual(
                             database.pop('Database_Description'),
                             database.pop('Database_Description_Welsh')),
                         'Classifications': db_classifications.classifications,
                         'Database_Type_Code': database_type_code})

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
            required('Internal_Category_Label_English'),
            required('Id'),
            required('Variable_Mnemonic'),
            required('Version'),

            # Sort_Order values are not validated as this is an optional field.
            optional('Sort_Order'),
            optional('External_Category_Label_English'),
            optional('External_Category_Label_Welsh'),
        ]
        category_rows = self.read_file(
            filename, columns,
            # There can only be one row for each Category_Code/Classification_Mnemonic combination.
            unique_combo_fields=['Category_Code', 'Classification_Mnemonic'])

        classification_to_cats = {}
        for cat, row_num in category_rows:
            classification_mnemonic = cat['Classification_Mnemonic']
            if self.classifications[classification_mnemonic].private['Is_Geographic']:
                raise ValueError(f'Reading {self.full_filename(filename)}:{row_num} '
                                 'found category for geographic classification '
                                 f'{classification_mnemonic}: all categories for geographic '
                                 'classifications must be in a separate lookup file')

            append_to_list_in_dict(classification_to_cats, classification_mnemonic, cat)

        categories = {}
        for classification_mnemonic, one_var_categories in classification_to_cats.items():
            num_cat_items = \
                self.classifications[classification_mnemonic].private['Number_Of_Category_Items']
            if num_cat_items and len(one_var_categories) != num_cat_items:
                self.recoverable_error(
                    f'Reading {self.full_filename(filename)} '
                    f'Unexpected number of categories for {classification_mnemonic}: '
                    f'expected {num_cat_items} but found {len(one_var_categories)}')

            welsh_cats = {cat['Category_Code']: cat['External_Category_Label_Welsh']
                          for cat in one_var_categories if cat['External_Category_Label_Welsh']}

            if welsh_cats:
                categories[classification_mnemonic] = Bilingual(None, welsh_cats)

        # Categories for geographic variables are supplied in a separate file.
        if not self.geography_file:
            logging.info('No geography file specified')
            return categories

        for class_name, geo_cats in read_geo_cats(self.geography_file).items():
            if class_name not in self.classifications:
                logging.info(f'Reading {self.geography_file}: found Welsh labels for unknown '
                             f'classification: {class_name}')
                continue

            if not self.classifications[class_name].private['Is_Geographic']:
                self.recoverable_error(f'Reading {self.geography_file}: found Welsh labels for '
                                       f'non geographic classification: {class_name}')
                continue

            welsh_names = {cd: nm.welsh_name for cd, nm in geo_cats.items() if nm.welsh_name}
            if geo_cats:
                categories[class_name] = Bilingual(None, welsh_names if welsh_names else None)

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
            required('Id'),
            required('Version'),
            required('Signed_Off_Flag', validate_fn=is_y_or_n),

            # Required for non-geographic variables but not always populated in source files
            optional('Statistical_Unit', validate_fn=isoneof(self.statistical_units.keys())),

            # Required for geographic variables but not yet populated
            optional('Geographic_Theme'),
            optional('Geographic_Coverage'),

            optional('Variable_Title_Welsh'),
            optional('Variable_Description_Welsh'),
            optional('Variable_Mnemonic_2011'),
            optional('Comparability_Comments'),
            optional('Comparability_Comments_Welsh'),
            optional('Uk_Comparison_Comments'),
            optional('Uk_Comparison_Comments_Welsh'),
            optional('Geographic_Theme_Welsh'),
            optional('Geographic_Coverage_Welsh'),
            optional('Topic_Mnemonic', validate_fn=isoneof(self.topics.keys())),
            optional('Number_Of_Classifications'),
            optional('Quality_Statement_Text'),
            optional('Quality_Summary_URL'),
        ]
        variable_rows = self.read_file(filename, columns)

        variable_mnemonics = [v.data['Variable_Mnemonic'] for v in variable_rows]
        variable_to_source_questions = self.load_variable_to_questions(variable_mnemonics)

        en_geo_fields = {'Geographic_Theme', 'Geographic_Coverage'}
        all_geo_fields = en_geo_fields | {'Geographic_Theme_Welsh',
                                          'Geographic_Coverage_Welsh'}
        variables = {}
        for variable, row_num in variable_rows:
            # Ensure that non-geographic variables do not have geographic values set.
            is_geographic = variable['Variable_Type_Code'] == GEOGRAPHIC_VARIABLE_TYPE
            if not is_geographic:
                # This value is not always populated in source files
                # if not variable['Statistical_Unit']:
                #     raise ValueError(f'Reading {self.full_filename(filename)}:{row_num} '
                #                    f'no Statistical_Unit specified for non geographic variable: '
                #                    f'{variable["Variable_Mnemonic"]}')
                for geo_field in all_geo_fields:
                    if variable[geo_field]:
                        self.recoverable_error(f'Reading {self.full_filename(filename)}:{row_num} '
                                               f'{geo_field} specified for non geographic '
                                               f'variable: {variable["Variable_Mnemonic"]}')

            # These values are not yet populated in source files
            # else:
            #    for geo_field in en_geo_fields:
            #        if not variable[geo_field]:
            #            raise ValueError(f'Reading {self.full_filename(filename)}:{row_num} '
            #                             f'no {geo_field} specified for geographic variable: '
            #                             f'{variable["Variable_Mnemonic"]}')

            variable_title = Bilingual(
                variable.pop('Variable_Title'),
                variable.pop('Variable_Title_Welsh'))

            variable['Variable_Title'] = variable_title
            variable['Comparability_Comments'] = Bilingual(
                variable.pop('Comparability_Comments'),
                variable.pop('Comparability_Comments_Welsh'))
            variable['Uk_Comparison_Comments'] = Bilingual(
                variable.pop('Uk_Comparison_Comments'),
                variable.pop('Uk_Comparison_Comments_Welsh'))
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
                         'Version': variable['Version'],
                         'Variable_Description': Bilingual(
                             variable.pop('Variable_Description'),
                             variable.pop('Variable_Description_Welsh'))})
        return variables

    @property
    @lru_cache(maxsize=1)
    def classifications(self):
        """Load classifications."""
        filename = 'Classification.csv'
        columns = [
            required('Id'),
            required('Classification_Mnemonic', unique=True),
            required('Variable_Mnemonic', validate_fn=isoneof(self.variables.keys())),
            required('Internal_Classification_Label_English'),
            required('Security_Mnemonic', validate_fn=isoneof(self.security_classifications)),
            required('Version'),
            required('Signed_Off_Flag', validate_fn=is_y_or_n),

            optional('Number_Of_Category_Items', validate_fn=isnumeric),
            optional('External_Classification_Label_English'),
            optional('External_Classification_Label_Welsh'),
            optional('Mnemonic_2011'),
            optional('Parent_Classification_Mnemonic'),
            optional('Default_Classification_Flag'),
            optional('Flat_Classification_Flag'),
        ]
        classification_rows = self.read_file(filename, columns)

        classification_mnemonics = [c.data['Classification_Mnemonic'] for c in classification_rows]
        classification_to_topics = self.load_classification_to_topics(classification_mnemonics)
        classification_to_codebook = self.load_class_to_codebook_mnemonic(classification_mnemonics)

        classifications = {}
        for classification, row_num in classification_rows:
            variable_mnemonic = classification.pop('Variable_Mnemonic')
            classification_mnemonic = classification.pop('Classification_Mnemonic')
            if self.variables[variable_mnemonic].private['Is_Geographic']:
                raise ValueError(f'Reading {self.full_filename(filename)}:{row_num} '
                                 f'{classification_mnemonic} has a geographic variable '
                                 f'{variable_mnemonic} which is not allowed')

            ons_variable = self.variables[variable_mnemonic]
            classification['ONS_Variable'] = ons_variable
            classification['Topics'] = classification_to_topics.get(classification_mnemonic, [])

            internal_label = classification.pop('Internal_Classification_Label_English')
            external_label = classification.pop('External_Classification_Label_English')
            if not external_label:
                external_label = internal_label

            # Ensure that if a classification is public that the associated variable is public.
            if classification['Security_Mnemonic'] == PUBLIC_SECURITY_MNEMONIC:
                variable = classification['ONS_Variable']
                if variable.private['Security_Mnemonic'] != PUBLIC_SECURITY_MNEMONIC:
                    raise ValueError(f'Reading {self.full_filename(filename)}:{row_num} '
                                     f'Public classification {classification_mnemonic} has '
                                     f'non-public variable {variable_mnemonic}')

            codebook_mnemonic = classification_to_codebook.get(classification_mnemonic,
                                                               classification_mnemonic)

            # Discard the Parent_Classification_Mnemonic. It can be obtained via the codebook and
            # the value may be ambiguous since some classifications are renamed using the
            # Codebook_Mnemonic from Category_Mapping.csv.
            del classification['Parent_Classification_Mnemonic']
            del classification['Signed_Off_Flag']
            del classification['Flat_Classification_Flag']
            del classification['Id']

            num_cat_items = classification.pop('Number_Of_Category_Items')
            num_cat_items = int(num_cat_items) if num_cat_items else 0

            classifications[classification_mnemonic] = BilingualDict(
                classification,
                # The private fields and not included in the English/Welsh variants of datasets.
                # They are used later in processing and included in different parts of the metadata
                # hierarchy.
                private={
                    'Number_Of_Category_Items': num_cat_items,
                    'Security_Mnemonic': classification.pop('Security_Mnemonic'),
                    'Classification_Label': Bilingual(
                        external_label,
                        classification.pop('External_Classification_Label_Welsh')),
                    'Variable_Mnemonic': variable_mnemonic,
                    'Variable_Description': ons_variable.private['Variable_Description'],
                    'Is_Geographic': False,
                    'Codebook_Mnemonic': codebook_mnemonic})

        # Every geographic variable must have a corresponding classification with the same
        # mnemonic. This is due to the fact that the dataset specifies a geographic variable
        # rather than a classification. Automatically create a classification for each geographic
        # variable.
        for variable_mnemonic, variable in self.variables.items():
            if variable.private['Is_Geographic']:
                logging.debug('Creating classification for geographic variable: '
                              f'{variable_mnemonic}')
                classifications[variable_mnemonic] = BilingualDict(
                    {
                        'Mnemonic_2011': None,
                        'Default_Classification_Flag': None,
                        'Version': variable.private['Version'],
                        'ONS_Variable': variable,
                        'Topics': [],
                    },
                    private={
                        'Number_Of_Category_Items': 0,
                        'Security_Mnemonic': variable.private['Security_Mnemonic'],
                        'Classification_Label': variable.private['Variable_Title'],
                        'Variable_Mnemonic': variable_mnemonic,
                        'Variable_Description': variable.private['Variable_Description'],
                        'Is_Geographic': True,
                        'Codebook_Mnemonic': variable_mnemonic})

        return classifications

    @property
    @lru_cache(maxsize=1)
    def observation_types(self):
        """Load observation types."""
        columns = [
            required('Observation_Type_Code', unique=True),
            required('Observation_Type_Label'),
            required('Id'),

            optional('Observation_Type_Description'),
            optional('Decimal_Places', validate_fn=isnumeric),
            optional('Prefix'),
            optional('Suffix'),
            optional('FillTrailingSpaces', validate_fn=is_y_or_n),
            optional('NegativeSign'),
        ]
        observation_type_rows = self.read_file('Observation_Type.csv', columns)

        observation_types = {}
        for observation_type, _ in observation_type_rows:
            del observation_type['Id']
            observation_types[observation_type['Observation_Type_Code']] = \
                BilingualDict(observation_type)

        return observation_types

    @property
    @lru_cache(maxsize=1)
    def database_types(self):
        """Load database types."""
        columns = [
            required('Database_Type_Code', unique=True),
            required('Database_Type_Description'),
            required('Id'),
        ]
        filename = 'Database_Type.csv'
        database_type_rows = self.read_file(filename, columns)

        database_types = {}
        for database_type, _ in database_type_rows:
            del database_type['Id']
            database_types[database_type['Database_Type_Code']] = BilingualDict(database_type)

        # TABULAR_DATABASE_TYPE must be defined as this is used to validate other data.
        if TABULAR_DATABASE_TYPE not in database_types:
            raise ValueError(f'{TABULAR_DATABASE_TYPE} not found as Database_Type_Code for any '
                             f'entry in {self.full_filename(filename)}')

        return database_types

    def load_database_to_classifications(self, database_mnemonics):
        """
        Load the variables associated with each database.

        This involves reading the Database_Variable.csv file which identifies the variables
        associated with each database, identifying the classifications associated with
        each variable and identifying the geographic variable with Lowest_Geog_Variable_Flag set
        to Y.
        """
        filename = 'Database_Variable.csv'
        columns = [
            required('Variable_Mnemonic', validate_fn=isoneof(self.variables.keys())),
            required('Database_Mnemonic', validate_fn=isoneof(database_mnemonics)),
            optional('Classification_Mnemonic', validate_fn=isoneof(self.classifications.keys())),
            required('Id'),
            required('Version'),

            optional('Lowest_Geog_Variable_Flag', validate_fn=isoneof(['Y', 'N'])),
            # No action is currently taken on these fields
            optional('Source_Classification_Flag', validate_fn=isoneof(['Y', 'N'])),
            optional('Cantabular_Public_Flag', validate_fn=isoneof(['Y', 'N'])),
        ]
        database_variable_rows = self.read_file(
            filename, columns,
            # There can only be one row for each Variable_Mnemonic/Database_Mnemonic combination.
            unique_combo_fields=['Variable_Mnemonic', 'Database_Mnemonic',
                                 'Classification_Mnemonic'])

        db_to_raw_vars = {}
        for db_var, _ in database_variable_rows:
            append_to_list_in_dict(db_to_raw_vars, db_var['Database_Mnemonic'], db_var)

        variable_to_classifications = dict()
        for classification_mnemonic, classification in self.classifications.items():
            variable_mnemonic = classification.private['Variable_Mnemonic']
            if variable_mnemonic not in variable_to_classifications:
                variable_to_classifications[variable_mnemonic] = set()
            variable_to_classifications[variable_mnemonic].add(classification_mnemonic)

        database_to_classifications = {}
        for database_mnemonic, db_vars in db_to_raw_vars.items():
            lowest_geog_var = None
            classifications = set()
            contains_geo_vars = False
            for db_var in db_vars:
                database_mnemonic = db_var['Database_Mnemonic']
                variable_mnemonic = db_var['Variable_Mnemonic']
                classification_mnemonic = db_var['Classification_Mnemonic']

                is_geographic = self.variables[variable_mnemonic].private['Is_Geographic']
                if is_geographic:
                    contains_geo_vars = True

                if db_var['Lowest_Geog_Variable_Flag'] == 'Y':
                    if not is_geographic:
                        self.recoverable_error(
                            f'Reading {self.full_filename(filename)} '
                            'Lowest_Geog_Variable_Flag set on non-geographic variable'
                            f' {variable_mnemonic} for database {database_mnemonic}')
                    elif lowest_geog_var:
                        self.recoverable_error(
                            f'Reading {self.full_filename(filename)} '
                            f'Lowest_Geog_Variable_Flag set on {variable_mnemonic} '
                            f'and {lowest_geog_var} for database {database_mnemonic}')
                    else:
                        lowest_geog_var = variable_mnemonic

                # Add the specific classification to the database if Classification_Mnemonic is set
                # else add all the classifications for the variable.
                if classification_mnemonic:
                    if classification_mnemonic not in \
                            variable_to_classifications.get(variable_mnemonic, set()):
                        self.recoverable_error(
                            f'Reading {self.full_filename(filename)} '
                            f'{classification_mnemonic} is unknown Classification_Mnemonic for '
                            f'Variable_Mnemonic {variable_mnemonic}')
                    else:
                        classifications.add(classification_mnemonic)
                else:
                    classifications = classifications.union(variable_to_classifications.get(
                        variable_mnemonic, set()))

            if not lowest_geog_var and contains_geo_vars:
                self.recoverable_error(f'Reading {self.full_filename(filename)} '
                                       'Lowest_Geog_Variable_Flag not set on any geographic '
                                       f'variable for database {database_mnemonic}')

            database_to_classifications[database_mnemonic] = DatabaseClassifications(
                classifications=classifications, lowest_geog_variable=lowest_geog_var)

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
        for rel_ds, _ in related_dataset_rows:
            append_to_list_in_dict(ds_to_related_ds_mnemonics, rel_ds['Dataset_Mnemonic'],
                                   rel_ds['Related_Dataset_Mnemonic'])

        return ds_to_related_ds_mnemonics

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

    def load_dataset_to_variables(self, dataset_mnemonics):
        """
        Load variables associated with each dataset.

        Variables can be geographic or non-geographic. Geographic variables will not have
        Classification_Mnemonic or Processing_Priority set. If there are geographic variables then
        one of them will have Lowest_Geog_Variable_Flag set to Y.

        Each non-geographic variable will also have Classification_Mnemonic and Processing_Priority
        set. The processing priorities indicate the order of the classifications. The priorities
        for each dataset must be unique and sequential, starting from 1. The classifications are
        ordered based on the priorities.

        The geographic variable with Lowest_Geog_Variable_Flag set to Y (if present) is placed
        at the start of the classifications list. There will be a classification with the same
        mnemonic as each geographic variable.
        """
        filename = 'Dataset_Variable.csv'
        columns = [
            required('Dataset_Mnemonic', validate_fn=isoneof(dataset_mnemonics)),
            required('Id'),
            required('Variable_Mnemonic', validate_fn=isoneof(self.variables.keys())),

            optional('Classification_Mnemonic', validate_fn=isoneof(self.classifications.keys())),
            optional('Processing_Priority', validate_fn=isnumeric),
            optional('Lowest_Geog_Variable_Flag', validate_fn=isoneof({'Y', 'N'})),
        ]
        dataset_variable_rows = self.read_file(
            filename, columns,
            # There can only be one row for each Dataset_Mnemonic/Variable_Mnemonic
            # combination.
            unique_combo_fields=['Dataset_Mnemonic', 'Variable_Mnemonic'])

        ds_to_vars_builder = {}
        for ds_variable, row_num in dataset_variable_rows:
            dataset_mnemonic = ds_variable['Dataset_Mnemonic']
            variable_mnemonic = ds_variable['Variable_Mnemonic']
            if dataset_mnemonic not in ds_to_vars_builder:
                ds_to_vars_builder[dataset_mnemonic] = DatasetVarsBuilder(
                    dataset_mnemonic, self.full_filename(filename), self.classifications,
                    self.recoverable_error)
            vars_builder = ds_to_vars_builder[dataset_mnemonic]

            if self.variables[variable_mnemonic].private['Is_Geographic']:
                vars_builder.add_geographic_variable(ds_variable, row_num)
            else:
                vars_builder.add_non_geographic_variable(ds_variable, row_num)

        ds_to_variables = {}
        for dataset_mnemonic, vars_builder in ds_to_vars_builder.items():
            ds_to_variables[dataset_mnemonic] = vars_builder.dataset_variables()

        return ds_to_variables

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

    def load_class_to_codebook_mnemonic(self, classification_mnemonics):
        """
        Load codebook mnemonic associated with each classification.

        The codebook mnemonic is generally the same as the associated variable mnemonic for
        base variables and the same as the classification mnemonic for other classifications.
        It is the name used for variables in Cantabular codebooks.

        The Category_Mapping.csv file contains more fields than those listed here, but they are
        not required in the cantabular-metadata JSON files.
        """
        filename = 'Category_Mapping.csv'
        columns = [
            required('Classification_Mnemonic', validate_fn=isoneof(classification_mnemonics)),
            required('Codebook_Mnemonic'),
        ]
        rows = self.read_file(filename, columns)

        classification_to_codebook = {}
        codebook_to_classification = {}
        for row, row_num in rows:
            classification_mnemonic = row['Classification_Mnemonic']
            codebook_mnemonic = row['Codebook_Mnemonic']
            if classification_mnemonic not in classification_to_codebook:
                if codebook_mnemonic in codebook_to_classification:
                    self.recoverable_error(
                        f'Reading {self.full_filename(filename)}:{row_num} '
                        f'{codebook_mnemonic} is Codebook_Mnemonic for both '
                        f'{codebook_to_classification[codebook_mnemonic]} and '
                        f'{classification_mnemonic}')
                elif codebook_mnemonic != classification_mnemonic and \
                        codebook_mnemonic in classification_mnemonics:
                    self.recoverable_error(
                        f'Reading {self.full_filename(filename)}:{row_num} '
                        f'{codebook_mnemonic} is an invalid Codebook_Mnemonic for classification '
                        f'{classification_mnemonic} as it is already the Classification_Mnemonic '
                        'for another classification')
                else:
                    codebook_to_classification[codebook_mnemonic] = classification_mnemonic
                    classification_to_codebook[classification_mnemonic] = codebook_mnemonic
                    continue

                # Set the classification_to_codebook value to None and use this to avoid reporting
                # multiple identical errors for a given Classification_Mnemonic.
                logging.warning(f'Reading {self.full_filename(filename)}:{row_num} '
                                f'ignoring field Codebook_Mnemonic')
                classification_to_codebook[classification_mnemonic] = None
            elif classification_to_codebook[classification_mnemonic] and \
                    classification_to_codebook[classification_mnemonic] != codebook_mnemonic:
                self.recoverable_error(
                    f'Reading {self.full_filename(filename)}:{row_num} different '
                    'Codebook_Mnemonic values specified for classification '
                    f'{classification_mnemonic}: {codebook_mnemonic} and '
                    f'{classification_to_codebook[classification_mnemonic]}')

        # Set the codebook menemonic to the classification mnemonic in cases where an invalid
        # codebook mnemonic was provided.
        for classification_mnemonic, codebook_mnemonic in classification_to_codebook.items():
            if not codebook_mnemonic:
                classification_to_codebook[classification_mnemonic] = classification_mnemonic

        return classification_to_codebook
