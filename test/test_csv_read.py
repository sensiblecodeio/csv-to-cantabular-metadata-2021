import unittest.mock
import unittest
from ons_csv_to_ctb_json_read import required, optional, Reader

def mock_open(*args, **kargs):
  f_open = unittest.mock.mock_open(*args, **kargs)
  f_open.return_value.__iter__ = lambda self : iter(self.readline, '')
  return f_open


def isoneof(valid_values):
    valid_values_set = set(valid_values)

    def validate_fn(value):
        return value in valid_values_set

    return validate_fn

def raise_error(msg):
    raise ValueError(msg)

class TestCSVRead(unittest.TestCase):
    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""id,name,email,age
1,bob,bob@bob.com,40
2,bill,,50
""")
    def test_read_file(self, m):
        columns = [
            required('name'),
            optional('email'),
            required('age', validate_fn=isoneof(['40', '50'])),
            required('id'),
            ]
        data = Reader('file.csv', columns, raise_error).read()

        self.assertEqual(data, [
            ({'name': 'bob', 'email': 'bob@bob.com', 'age': '40', 'id': '1'}, 2),
            ({'name': 'bill', 'email': None, 'age': '50', 'id': '2'}, 3)])

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""id,name,email,age
1,bob,bob@bob.com,40
""")
    def test_extra_fields(self, m):
        columns = [
            required('name'),
            required('id'),
            ]
        data = Reader('file.csv', columns, raise_error).read()

        self.assertEqual(data, [
            ({'name': 'bob', 'id': '1'}, 2)])

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""name
bob
""")
    def test_missing_fields(self, m):
        columns = [
            required('name'),
            required('email'),
            required('id'),
            ]
        with self.assertRaisesRegex(ValueError, 'Reading file.csv: missing expected columns: email, id'):
            Reader('file.csv', columns, raise_error).read()

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""name,email
bob,bob@bob.com
bill,bill@bill.com,50
""")
    def test_too_many_columns(self, m):
        columns = [
            required('name'),
            required('email'),
            ]
        with self.assertRaisesRegex(ValueError, 'Reading file.csv: too many fields on row 3'):
            Reader('file.csv', columns, raise_error).read()

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""name,email
bob,bob@bob.com
bill
""")
    def test_too_few_columns(self, m):
        columns = [
            required('name'),
            required('email'),
            ]
        with self.assertRaisesRegex(ValueError, 'Reading file.csv: too few fields on row 3'):
            Reader('file.csv', columns, raise_error).read()

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""name
bob
bill
ben
""")
    def test_invalid_value(self, m):
        columns = [
            required('name', validate_fn=isoneof(['bob', 'bill'])),
            ]
        with self.assertRaisesRegex(ValueError, 'Reading file.csv:4 invalid value ben for name'):
            Reader('file.csv', columns, raise_error).read()

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""name
bob
bill
bob
""")
    def test_non_unique_value(self, m):
        columns = [
            required('name', unique=True),
            ]
        with self.assertRaisesRegex(ValueError, 'Reading file.csv:4 duplicate value bob for name'):
            Reader('file.csv', columns, raise_error).read()

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""name
bob
bill
bOb
""")
    def test_non_unique_value_case_insensitive(self, m):
        columns = [
            required('name', unique=True),
            ]
        with self.assertRaisesRegex(ValueError, 'Reading file.csv:4 duplicate value bOb for name'):
            Reader('file.csv', columns, raise_error).read()



    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""name,email
bob,bob@bob.com
,
,
""")
    def test_empty_rows(self, m):
        columns = [
            required('name'),
            required('email'),
            ]
        data = Reader('file.csv', columns, raise_error).read()

        self.assertEqual(data, [
            ({'name': 'bob', 'email': 'bob@bob.com'}, 2)])

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""name,id
bob,1
bill ,2
 barbara,3
""")
    def test_whitespace(self, m):
        columns = [
            required('name'),
            required('id'),
            ]
        data = Reader('file.csv', columns, raise_error).read()

        self.assertEqual(data, [
            ({'name': 'bob', 'id': '1'}, 2),
            ({'name': 'bill', 'id': '2'}, 3),
            ({'name': 'barbara', 'id': '3'}, 4)])

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""name,id
bob,1
bob,2
bill,1
bill,2
bob,1
""")
    def test_unique_combos(self, m):
        columns = [
            required('name'),
            required('id'),
            ]
        with self.assertRaisesRegex(ValueError, 'Reading file.csv:6 duplicate value combo bob/1 for name/id'):
            Reader('file.csv', columns, raise_error, unique_combo_fields=['name', 'id']).read()

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""id,Dataset_Mnemonic
1,TS1
2,TT1
3,SS1
4,TS2
5,T
6,TX1
""")
    def test_dataset_filter(self, m):
        columns = [
            required('id'),
            required('Dataset_Mnemonic'),
            ]

        with self.assertLogs(level='INFO') as cm:
            data = Reader('file.csv', columns, raise_error, dataset_filter='TS, ,TX ').read()

        self.assertEqual(data, [
            ({'Dataset_Mnemonic': 'TS1', 'id': '1'}, 2),
            ({'Dataset_Mnemonic': 'TS2', 'id': '4'}, 5),
            ({'Dataset_Mnemonic': 'TX1', 'id': '6'}, 7)])

        self.assertEqual(1, len(cm.output))
        self.assertRegex(cm.output[0], r"file.csv dropped 3 records related to datasets with Dataset_Mnemonics that do not start with one of: \['TS', 'TX']")


if __name__ == '__main__':
    unittest.main()
