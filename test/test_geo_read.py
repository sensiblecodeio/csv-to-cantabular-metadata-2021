import unittest.mock
import unittest
from ons_csv_to_ctb_json_geo import read_geo_cats, AreaName

def mock_open(*args, **kargs):
  f_open = unittest.mock.mock_open(*args, **kargs)
  f_open.return_value.__iter__ = lambda self : iter(self.readline, '')
  return f_open


class TestGeoRead(unittest.TestCase):
    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA11cd,LAD22cd,LAD22nm,LAD22nmw,COUNTRY22cd,COUNTRY22nm
OA1,LAD1,LAD1 Name,LAD1 Name (Welsh),COUNTRY1,COUNTRY1 Name
OA2,LAD1,LAD1 Name,LAD1 Name (Welsh),COUNTRY1,COUNTRY1 Name
OA3,LAD2,LAD2 Name,LAD2 Name (Welsh),COUNTRY1,COUNTRY1 Name
OA3,LAD2,LAD2 Name,LAD2 Name (Welsh),COUNTRY1,COUNTRY1 Name
OA5,LAD3,LAD3 Name,LAD3 Name (Welsh),COUNTRY1,COUNTRY1 Name
OA6,LAD4,LAD4 Name,,COUNTRY1,COUNTRY1 Name
OA7,LAD5,LAD5 Name,LAD5 Name (Welsh),COUNTRY1,COUNTRY1 Name
""")
    def test_read_file(self, m):
        data = read_geo_cats('file.csv')
        self.assertEqual(data,
            {
                'lad': {
                    'LAD1': AreaName('LAD1 Name', 'LAD1 Name (Welsh)'),
                    'LAD2': AreaName('LAD2 Name', 'LAD2 Name (Welsh)'),
                    'LAD3': AreaName('LAD3 Name', 'LAD3 Name (Welsh)'),
                    'LAD4': AreaName('LAD4 Name', ''),
                    'LAD5': AreaName('LAD5 Name', 'LAD5 Name (Welsh)')
                },
                'country': {
                    'COUNTRY1': AreaName('COUNTRY1 Name', ''),
                },
            })

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data=""" LAD22cd , LAD22nm,LAD22nmw
 LAD1 , LAD1 Name,LAD1 Name (Welsh)
 LAD2 , LAD2 Name,LAD2 Name (Welsh)
 LAD3 , LAD3 Name,LAD3 Name (Welsh)
""")
    def test_whitespace_stripping(self, m):
        data = read_geo_cats('file.csv')
        self.assertEqual(data,
            {'lad': {
                'LAD1': AreaName('LAD1 Name', 'LAD1 Name (Welsh)'),
                'LAD2': AreaName('LAD2 Name', 'LAD2 Name (Welsh)'),
                'LAD3': AreaName('LAD3 Name', 'LAD3 Name (Welsh)'),
                }
            })

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""lad22cd,LAD22NM,lad22NMw
LAD1,LAD1 Name,LAD1 Name (Welsh)
""")
    def test_heading_case_insensitivity(self, m):
        data = read_geo_cats('file.csv')
        self.assertEqual(data,
            {'lad': {
                'LAD1': AreaName('LAD1 Name', 'LAD1 Name (Welsh)'),
                }
            })

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""AbyZ_-422cd,AbyZ_-422nm,AbyZ_-422nmw
1,Name,Name (Welsh)
""")
    def test_valid_varname_characters(self, m):
        data = read_geo_cats('file.csv')
        self.assertEqual(data,
            {'abyz_-4': {
                '1': AreaName('Name', 'Name (Welsh)'),
                }
            })

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA11cd,LAD22cd,LAD22nm,LAD22nmw,COUNTRY22cd,COUNTRY22nm
OA1,LAD1,LAD1 Name,LAD1 Name (Welsh),COUNTRY1,COUNTRY1 Name,extra
""")
    def test_too_many_columns(self, m):
        with self.assertRaisesRegex(ValueError, 'Reading file.csv: too many fields on row 2'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA11cd,LAD22cd,LAD22nm,LAD22nmw,COUNTRY22cd,COUNTRY22nm
OA1,LAD1,LAD1 Name,LAD1 Name (Welsh),COUNTRY1
""")
    def test_too_few_columns(self, m):
        with self.assertRaisesRegex(ValueError, 'Reading file.csv: too few fields on row 2'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD22cd,LAD22nm,LAD22nmw
LAD1,LAD1 Name,LAD1 Name (Welsh)
LAD2,LAD2 Name,LAD2 Name (Welsh)
LAD2,LAD2 Name,LAD2 Name (Welsh)
LAD3,LAD3 Name,LAD3 Name (Welsh)
LAD3,LAD3 Name,Other Name (Welsh)
""")
    def test_different_welsh_names(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: different Welsh name for code LAD3 of lad: "Other Name \(Welsh\)" and "LAD3 Name \(Welsh\)"$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD22cd,LAD22nm,LAD22nmw
LAD1,LAD1 Name,LAD1 Name (Welsh)
LAD2,LAD2 Name,LAD2 Name (Welsh)
LAD2,Other Name,LAD2 Name (Welsh)
""")
    def test_different_names(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: different name for code LAD2 of lad: "Other Name" and "LAD2 Name"$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD22cd,LAD22nm,LAD22nmw,LAD22nm,LAD22nmw
""")
    def test_duplicate_column_names(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: duplicate case insensitive column names: lad22nm, lad22nmw$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA22cd,LA1Dcd
""")
    def test_invalid_varname_missing_year(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: invalid code column name: LA1Dcd$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA22cd,LA^22cd
""")
    def test_invalid_varname_character(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: invalid code column name: LA\^22cd$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA22cd,LA1Dcd
""")
    def test_invalid_code_column_name(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: invalid code column name: LA1Dcd$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD11cd,LAD22cd
""")
    def test_multiple_code_columns(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: multiple code columns found for lad: LAD22cd and LAD11cd$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD11cd,LAD11nm,LAD11nmw,OA11nm,COUNTRY11nmw,DISTRICT22cd,DISTRICT22nmw
""")
    def test_unexpected_fields(self, m):
        with self.assertRaisesRegex(ValueError, '^Unexpected fieldnames: COUNTRY11nmw, DISTRICT22nmw, OA11nm'):
            read_geo_cats('file.csv')


if __name__ == '__main__':
    unittest.main()
