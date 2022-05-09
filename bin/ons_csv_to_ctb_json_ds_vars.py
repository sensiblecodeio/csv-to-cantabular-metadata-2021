"""Build data structure that represents relationship between dataset and variables."""
import logging
from collections import namedtuple

DatasetVariables = namedtuple('DatasetVariables', 'classifications alternate_geog_variables')


class DatasetVarsBuilder():
    """Utility class to validate and build dataset variables."""

    def __init__(self, dataset_mnemonic, filename, all_classifications):
        """Initialise DatasetVarsBuilder object."""
        self.lowest_geog_variable = None
        self.alternate_geog_variables = []
        self.classifications = []
        self.processing_priorities = []
        self.dataset_mnemonic = dataset_mnemonic
        self.filename = filename
        self.all_classifications = all_classifications

    def add_geographic_variable(self, variable):
        """Add geographic variable ensuring data integrity."""
        variable_mnemonic = variable['Variable_Mnemonic']
        classification_mnemonic = variable['Classification_Mnemonic']
        if classification_mnemonic:
            raise ValueError(f'Reading {self.filename} '
                             'Classification_Mnemonic must not be specified for '
                             f'geographic variable {variable_mnemonic} in dataset '
                             f'{self.dataset_mnemonic}')
        if variable['Processing_Priority']:
            raise ValueError(f'Reading {self.filename} '
                             'Processing_Priority must not be specified for geographic'
                             f' variable {variable_mnemonic} in dataset '
                             f'{self.dataset_mnemonic}')
        if variable['Lowest_Geog_Variable_Flag'] == 'Y':
            if self.lowest_geog_variable:
                raise ValueError(f'Reading {self.filename} '
                                 'Lowest_Geog_Variable_Flag set on variable '
                                 f'{variable_mnemonic} and '
                                 f'{self.lowest_geog_variable} for dataset '
                                 f'{self.dataset_mnemonic}')
            self.lowest_geog_variable = variable['Variable_Mnemonic']
        else:
            self.alternate_geog_variables.append(variable['Variable_Mnemonic'])

    def add_non_geographic_variable(self, variable):
        """Add non-geographic variable ensuring data integrity."""
        variable_mnemonic = variable['Variable_Mnemonic']
        classification_mnemonic = variable['Classification_Mnemonic']
        if not classification_mnemonic:
            msg = (f'Reading {self.filename} '
                   'Classification must be specified for non-geographic '
                   f'{variable_mnemonic} in dataset {self.dataset_mnemonic}')
            # raise ValueError(msg)
            logging.warning(msg)
            logging.warning(f'dropping record at {self.filename}')
            return

        if variable['Lowest_Geog_Variable_Flag'] == 'Y':
            raise ValueError(f'Reading {self.filename} '
                             'Lowest_Geog_Variable_Flag set on non-geographic variable'
                             f' {variable_mnemonic} for dataset {self.dataset_mnemonic}')

        classification = self.all_classifications[classification_mnemonic]
        if classification.private['Variable_Mnemonic'] != variable_mnemonic:
            raise ValueError(f'Reading {self.filename} Invalid '
                             f'classification {classification_mnemonic} '
                             f'specified for variable {variable_mnemonic} '
                             f'in dataset {self.dataset_mnemonic}')
        if not variable['Processing_Priority']:
            raise ValueError(f'Reading {self.filename} '
                             'Processing_Priority not specified for classification '
                             f'{classification_mnemonic} in dataset '
                             f'{self.dataset_mnemonic}')
        self.classifications.append(variable['Classification_Mnemonic'])
        self.processing_priorities.append(int(variable['Processing_Priority']))

    def dataset_variables(self):
        """Return dataset classifications and alternate geographic variables for each dataset."""
        if self.alternate_geog_variables and not self.lowest_geog_variable:
            raise ValueError(f'Reading {self.filename} '
                             'Lowest_Geog_Variable_Flag not set on any geographic variables '
                             f'for dataset {self.dataset_mnemonic}')

        if set(self.processing_priorities) != set(range(1, len(self.processing_priorities) + 1)):
            msg = (f'Reading {self.filename} Invalid processing_priorities '
                   f'{self.processing_priorities} for dataset {self.dataset_mnemonic}')
            # raise ValueError(msg)
            logging.warning(msg)

        classifications = [c for _, c in sorted(zip(self.processing_priorities,
                                                    self.classifications))]

        if self.lowest_geog_variable:
            classifications.insert(0, self.lowest_geog_variable)

        geo_vars = sorted(self.alternate_geog_variables) if self.alternate_geog_variables else None

        return DatasetVariables(classifications, geo_vars)
