import unittest.mock
import unittest
from ons_csv_to_ctb_json_geo import read_geo_cats, AreaName

def mock_open(*args, **kargs):
  f_open = unittest.mock.mock_open(*args, **kargs)
  f_open.return_value.__iter__ = lambda self : iter(self.readline, '')
  return f_open


class TestGeoRead(unittest.TestCase):
    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA11CD,LAD22CD,LAD22NM,LAD22NMW,COUNTRY22CD,COUNTRY22NM
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
                'LAD': {
                    'LAD1': AreaName('LAD1 Name', 'LAD1 Name (Welsh)'),
                    'LAD2': AreaName('LAD2 Name', 'LAD2 Name (Welsh)'),
                    'LAD3': AreaName('LAD3 Name', 'LAD3 Name (Welsh)'),
                    'LAD4': AreaName('LAD4 Name', ''),
                    'LAD5': AreaName('LAD5 Name', 'LAD5 Name (Welsh)')
                },
                'COUNTRY': {
                    'COUNTRY1': AreaName('COUNTRY1 Name', ''),
                },
            })

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data=""" LAD22CD , LAD22NM,LAD22NMW 
 LAD1 , LAD1 Name,LAD1 Name (Welsh) 
 LAD2 , LAD2 Name,LAD2 Name (Welsh) 
 LAD3 , LAD3 Name,LAD3 Name (Welsh) 
""")
    def test_whitespace_stripping(self, m):
        data = read_geo_cats('file.csv')
        self.assertEqual(data,
            {'LAD': {
                'LAD1': AreaName('LAD1 Name', 'LAD1 Name (Welsh)'),
                'LAD2': AreaName('LAD2 Name', 'LAD2 Name (Welsh)'),
                'LAD3': AreaName('LAD3 Name', 'LAD3 Name (Welsh)'),
                }
            })

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""AbyZ_-422CD,AbyZ_-422NM,AbyZ_-422NMW
1,Name,Name (Welsh)
""")
    def test_valid_varname_characters(self, m):
        data = read_geo_cats('file.csv')
        self.assertEqual(data,
            {'AbyZ_-4': {
                '1': AreaName('Name', 'Name (Welsh)'),
                }
            })

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA11CD,LAD22CD,LAD22NM,LAD22NMW,COUNTRY22CD,COUNTRY22NM
OA1,LAD1,LAD1 Name,LAD1 Name (Welsh),COUNTRY1,COUNTRY1 Name,extra
""")
    def test_too_many_columns(self, m):
        with self.assertRaisesRegex(ValueError, 'Reading file.csv: too many fields on line 2'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA11CD,LAD22CD,LAD22NM,LAD22NMW,COUNTRY22CD,COUNTRY22NM
OA1,LAD1,LAD1 Name,LAD1 Name (Welsh),COUNTRY1
""")
    def test_too_few_columns(self, m):
        with self.assertRaisesRegex(ValueError, 'Reading file.csv: too few fields on line 2'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD22CD,LAD22NM,LAD22NMW
LAD1,LAD1 Name,LAD1 Name (Welsh)
LAD2,LAD2 Name,LAD2 Name (Welsh)
LAD2,LAD2 Name,LAD2 Name (Welsh)
LAD3,LAD3 Name,LAD3 Name (Welsh)
LAD3,LAD3 Name,Other Name (Welsh)
""")
    def test_different_welsh_names(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: different Welsh name for code LAD3 of LAD: "Other Name \(Welsh\)" and "LAD3 Name \(Welsh\)"$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD22CD,LAD22NM,LAD22NMW
LAD1,LAD1 Name,LAD1 Name (Welsh)
LAD2,LAD2 Name,LAD2 Name (Welsh)
LAD2,Other Name,LAD2 Name (Welsh)
""")
    def test_different_names(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: different name for code LAD2 of LAD: "Other Name" and "LAD2 Name"$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD22CD,LAD22NM,LAD22NMW,LAD22NM,LAD22NMW
""")
    def test_duplicate_column_names(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: duplicate column names: LAD22NM, LAD22NMW$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD22CD,LAD22NM,LAD22NMW,LAD22NM,LAD22NMW
""")
    def test_duplicate_column_names(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: duplicate column names: LAD22NM, LAD22NMW$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA22CD,LA1DCD
""")
    def test_invalid_varname_missing_year(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: invalid code column name: LA1DCD$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA22CD,LA^22CD
""")
    def test_invalid_varname_character(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: invalid code column name: LA\^22CD$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""OA22CD,LA1DCD
""")
    def test_invalid_code_column_name(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: invalid code column name: LA1DCD$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD11CD,LAD22CD
""")
    def test_multiple_code_columns(self, m):
        with self.assertRaisesRegex(ValueError, '^Reading file.csv: multiple code columns found for LAD: LAD22CD and LAD11CD$'):
            read_geo_cats('file.csv')

    @unittest.mock.patch('builtins.open', new_callable=mock_open, read_data="""LAD11CD,LAD11NM,LAD11NMW,OA11NM,COUNTRY11NMW,DISTRICT22CD,DISTRICT22NMW
""")
    def test_unexpected_fields(self, m):
        with self.assertRaisesRegex(ValueError, '^Unexpected fieldnames: COUNTRY11NMW, DISTRICT22NMW, OA11NM'):
            read_geo_cats('file.csv')


if __name__ == '__main__':
    unittest.main()
