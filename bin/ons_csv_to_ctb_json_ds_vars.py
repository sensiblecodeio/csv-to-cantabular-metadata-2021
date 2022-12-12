"""Build data structure that represents relationship between dataset and variables."""
import logging
from collections import namedtuple

TABULAR_DATABASE_TYPE = 'AGGDATA'

DatasetVariables = namedtuple('DatasetVariables',
                              'classifications alternate_geog_variables databases')


class DatasetVarsBuilder():
    """Utility class to validate and build dataset variables."""

    def __init__(self, dataset_mnemonic, filename, all_classifications, all_databases,
                 all_variables, recoverable_error):
        """Initialise DatasetVarsBuilder object."""
        self.lowest_geog_variable = None
        self.alternate_geog_variables = []
        self.classifications = []
        self.processing_priorities = []
        self.dataset_mnemonic = dataset_mnemonic
        self.filename = filename
        self.all_classifications = all_classifications
        self.all_databases = all_databases
        self.all_variables = all_variables
        self.recoverable_error = recoverable_error
        self.databases = set()

    def add_geographic_variable(self, variable, row_num):
        """Add geographic variable ensuring data integrity."""
        variable_mnemonic = variable['Variable_Mnemonic']
        classification_mnemonic = variable['Classification_Mnemonic']
        if classification_mnemonic:
            self.recoverable_error(f'Reading {self.filename}:{row_num} '
                                   'Classification_Mnemonic must not be specified for '
                                   f'geographic variable {variable_mnemonic} in dataset '
                                   f'{self.dataset_mnemonic}')
        if variable['Processing_Priority']:
            self.recoverable_error(f'Reading {self.filename}:{row_num} '
                                   'Processing_Priority must not be specified for geographic'
                                   f' variable {variable_mnemonic} in dataset '
                                   f'{self.dataset_mnemonic}')
        if variable['Lowest_Geog_Variable_Flag'] == 'Y':
            if self.lowest_geog_variable:
                self.recoverable_error(f'Reading {self.filename}:{row_num} '
                                       'Lowest_Geog_Variable_Flag set on variable '
                                       f'{variable_mnemonic} and '
                                       f'{self.lowest_geog_variable} for dataset '
                                       f'{self.dataset_mnemonic}')
            else:
                self.lowest_geog_variable = variable_mnemonic
        self.alternate_geog_variables.append(variable_mnemonic)

        database_mnemonic = variable['Database_Mnemonic']
        database = self.all_databases[database_mnemonic]
        if variable_mnemonic not in database.private['Classifications']:
            self.recoverable_error(
                f'Reading {self.filename}:{row_num} '
                f'{self.dataset_mnemonic} has geographic variable {variable_mnemonic} '
                f'that is not in database {database_mnemonic}')

        self._add_database(database_mnemonic, row_num)

    def add_non_geographic_variable(self, variable, row_num):
        """Add non-geographic variable ensuring data integrity."""
        variable_mnemonic = variable['Variable_Mnemonic']
        classification_mnemonic = variable['Classification_Mnemonic']
        if not classification_mnemonic:
            self.recoverable_error(f'Reading {self.filename}:{row_num} '
                                   'Classification must be specified for non-geographic '
                                   f'{variable_mnemonic} in dataset {self.dataset_mnemonic}')
            logging.warning(f'Reading {self.filename}:{row_num} dropping record')
            return

        if variable['Lowest_Geog_Variable_Flag'] == 'Y':
            self.recoverable_error(f'Reading {self.filename}:{row_num} '
                                   'Lowest_Geog_Variable_Flag set on non-geographic variable '
                                   f'{variable_mnemonic} for dataset {self.dataset_mnemonic}')

        classification = self.all_classifications[classification_mnemonic]
        if classification.private['Variable_Mnemonic'] != variable_mnemonic:
            self.recoverable_error(f'Reading {self.filename}:{row_num} Invalid '
                                   f'classification {classification_mnemonic} '
                                   f'specified for variable {variable_mnemonic} '
                                   f'in dataset {self.dataset_mnemonic}')
            logging.warning(f'Reading {self.filename}:{row_num} dropping record')
            return

        if not variable['Processing_Priority']:
            self.recoverable_error(f'Reading {self.filename}:{row_num} '
                                   'Processing_Priority not specified for classification '
                                   f'{classification_mnemonic} in dataset '
                                   f'{self.dataset_mnemonic}')
            logging.warning(f'Reading {self.filename}:{row_num} using 0 for Processing_Priority')
            variable['Processing_Priority'] = 0

        self.classifications.append(variable['Classification_Mnemonic'])
        self.processing_priorities.append(int(variable['Processing_Priority']))

        database_mnemonic = variable['Database_Mnemonic']
        database = self.all_databases[database_mnemonic]
        if classification_mnemonic not in database.private['Classifications']:
            self.recoverable_error(
                f'Reading {self.filename}:{row_num} '
                f'{self.dataset_mnemonic} has classification {classification_mnemonic} '
                f'that is not in database {database_mnemonic}')

        self._add_database(database_mnemonic, row_num)

    def _add_database(self, database_mnemonic, row_num):
        database = self.all_databases[database_mnemonic]
        if database.private['Database_Type_Code'] == TABULAR_DATABASE_TYPE:
            self.recoverable_error(
                f'Reading {self.filename}:{row_num} {self.dataset_mnemonic} '
                f'has Database_Mnemonic {database_mnemonic} which has invalid '
                f'Database_Type_Code: {TABULAR_DATABASE_TYPE}')
        self.databases.add(database_mnemonic)

    def dataset_variables(self):
        """Return dataset classifications and alternate geographic variables for each dataset."""
        if self.alternate_geog_variables and not self.lowest_geog_variable:
            self.recoverable_error(f'Reading {self.filename} '
                                   'Lowest_Geog_Variable_Flag not set on any geographic variables '
                                   f'for dataset {self.dataset_mnemonic}')

        # Sort alternate_geog_variables based on order specified in Geography_Hierarchy_Order in
        # descending order, so that the variable with the highest value of
        # Geography_Hierarchy_Order comes first.
        self.alternate_geog_variables = [
            g for _, g in sorted(zip([self.all_variables[g].private['Geography_Hierarchy_Order']
                                      for g in self.alternate_geog_variables],
                                     self.alternate_geog_variables), reverse=True)]

        if self.alternate_geog_variables and self.all_variables[self.lowest_geog_variable] != \
                self.all_variables[self.alternate_geog_variables[-1]]:
            self.recoverable_error(
                f'Reading {self.filename} Lowest_Geog_Variable_Flag set on '
                f'{self.lowest_geog_variable} for dataset {self.dataset_mnemonic} but '
                f'{self.alternate_geog_variables[-1]} has a lower Geography_Hierarchy_Order')

        if set(self.processing_priorities) != set(range(1, len(self.processing_priorities) + 1)):
            self.recoverable_error(f'Reading {self.filename} '
                                   'Invalid processing_priorities '
                                   f'{self.processing_priorities} for dataset '
                                   f'{self.dataset_mnemonic}')

        classifications = [c for _, c in sorted(zip(self.processing_priorities,
                                                    self.classifications))]

        if self.lowest_geog_variable:
            classifications.insert(0, self.lowest_geog_variable)

        geo_vars = self.alternate_geog_variables if self.alternate_geog_variables else None

        return DatasetVariables(classifications, geo_vars, sorted(self.databases))
