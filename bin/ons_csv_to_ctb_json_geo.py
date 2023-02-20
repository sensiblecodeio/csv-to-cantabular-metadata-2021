"""Load geographic variable category labels from CSV file."""
import csv
import re
from collections import namedtuple

ColumnIndices = namedtuple('ColumnIndices', 'code name welsh_name')
AreaName = namedtuple('AreaName', 'name welsh_name')
GeoCats = namedtuple('GeoCats', 'source_file code_to_label')


CODE_SUFFIX = 'cd'
NAME_SUFFIX = 'nm'
WELSH_NAME_SUFFIX = 'nmw'


def read_geo_cats(filenames):
    """Read a list of geography lookup files and return the combined categories from all files."""
    data = {}
    for filename in filenames:
        for variable, geo_cats in read_file(filename).items():
            if variable not in data:
                data[variable] = geo_cats
            elif data[variable].code_to_label != geo_cats.code_to_label:
                raise ValueError(f'{data[variable].source_file} and {geo_cats.source_file} '
                                 f'contain different sets of categories for {variable}')

    return data


def read_file(filename):
    """
    Read a lookup file containing variable category codes, labels and Welsh labels.

    Each variable will have a cd (code) column. It may also have nm (name) and nmw (Welsh name)
    columns. The column names are expected to have the format (as a regular expression):
        <variable name><2 numerical digits for year><column type>
    And to match the regular expression:
        ^[a-zA-Z0-9_-]+[0-9][0-9](cd|nm|nmw)$

    Category names are returned for all variables with a nm column. Welsh category names are
    returned for all variables with a nmw column. The names are returned as a dict of dicts keyed
    on the variable name. Each sub-dict is keyed on the category code and each item is of type
    AreaName.

     - All fields have leading/trailing whitespace removed.
     - There must not be entries for a single variable with different years e.g. LAD11cd
       and LAD22cd.
     - If multiple lines in the file refer to the same category then the names must be consistent
       on all lines.
     - The column names are handled in a cases insensitive manner.

    """
    with open(filename, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        fieldnames = [v.strip() for v in next(reader)]
        var_to_columns = assign_columns_to_variables(filename, fieldnames)
        data = {var_name: GeoCats(source_file=filename, code_to_label={})
                for var_name in var_to_columns}

        for row_num, row in enumerate(reader, 2):
            if len(row) > len(fieldnames):
                raise ValueError(f'Reading {filename}: too many fields on row {row_num}')
            if len(row) < len(fieldnames):
                raise ValueError(f'Reading {filename}: too few fields on row {row_num}')

            for geo, columns in var_to_columns.items():
                code = row[columns.code].strip()
                name = row[columns.name].strip() if columns.name else ""
                welsh_name = row[columns.welsh_name].strip() if columns.welsh_name else ""

                if code not in data[geo].code_to_label:
                    data[geo].code_to_label[code] = AreaName(name=name, welsh_name=welsh_name)
                    continue
                if data[geo].code_to_label[code].name != name:
                    raise ValueError(
                        f'Reading {filename}: different name for code {code} of '
                        f'{geo}: "{name}" and "{data[geo].code_to_label[code].name}"')
                if data[geo].code_to_label[code].welsh_name != welsh_name:
                    raise ValueError(
                        f'Reading {filename}: different Welsh name for code {code} of '
                        f'{geo}: "{welsh_name}" and "{data[geo].code_to_label[code].welsh_name}"')

    return data


def assign_columns_to_variables(filename, fieldnames):
    """Identify columns associated with each variable."""
    lc_fieldnames = [fn.lower() for fn in fieldnames]

    def original_case(fieldname):
        return fieldnames[lc_fieldnames.index(fieldname)]

    fieldnames_set = set(lc_fieldnames)
    if len(fieldnames_set) != len(fieldnames):
        duplicates = {fn for fn in lc_fieldnames if lc_fieldnames.count(fn) > 1}
        raise ValueError(f'Reading {filename}: duplicate case insensitive column names: '
                         f'{", ".join(sorted(duplicates))}')

    code_fields = {fn for fn in lc_fieldnames if fn.endswith(CODE_SUFFIX)}
    fields_to_process = fieldnames_set - code_fields
    processed_code_fields = dict()
    code_regex = re.compile(f'([a-zA-Z0-9_-]+)([0-9][0-9]){CODE_SUFFIX}')

    var_to_columns = {}
    for fieldname in sorted(code_fields):
        match = code_regex.fullmatch(fieldname)
        if not match:
            raise ValueError(f'Reading {filename}: invalid code column name: '
                             f'{original_case(fieldname)}')

        var_name = match.group(1)
        year = match.group(2)

        if var_name in processed_code_fields:
            raise ValueError(f'Reading {filename}: multiple code columns found for '
                             f'{var_name}: {original_case(fieldname)} and '
                             f'{original_case(processed_code_fields[var_name])}')
        processed_code_fields[var_name] = fieldname

        # Some geographic variables will not have a name fields e.g. OA. Some will not have a
        # Welsh name field. But if a variable does have a Welsh name field then it is expected to
        # have a name field.
        name_field = var_name + year + NAME_SUFFIX
        if name_field not in fields_to_process:
            continue
        fields_to_process.remove(name_field)
        name = lc_fieldnames.index(name_field)

        welsh_name = None
        welsh_name_field = var_name + year + WELSH_NAME_SUFFIX
        if welsh_name_field in fields_to_process:
            fields_to_process.remove(welsh_name_field)
            welsh_name = lc_fieldnames.index(welsh_name_field)

        var_to_columns[var_name] = ColumnIndices(
            code=lc_fieldnames.index(fieldname),
            name=name,
            welsh_name=welsh_name)

    if fields_to_process:
        raise ValueError(f'Reading {filename}: unexpected fieldnames: '
                         f'{", ".join(sorted([original_case(f) for f in fields_to_process]))}')

    return var_to_columns
