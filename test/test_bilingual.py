import unittest.mock
import unittest
from ons_csv_to_ctb_json_bilingual import Bilingual, BilingualDict


class TestBilingual(unittest.TestCase):
    def test_bilingual(self):
        data = Bilingual('en', 'cy')
        self.assertEqual(data.english(), 'en')
        self.assertEqual(data.welsh(), 'cy')

    def test_missing_welsh(self):
        data = Bilingual('en', '')
        self.assertEqual(data.english(), 'en')
        self.assertEqual(data.welsh(), 'en')

        data = Bilingual('en', '', default_to_english=True)
        self.assertEqual(data.english(), 'en')
        self.assertEqual(data.welsh(), 'en')

        data = Bilingual('en', '', default_to_english=False)
        self.assertEqual(data.english(), 'en')
        self.assertEqual(data.welsh(), None)

    def test_bilingual_dict(self):
        data = BilingualDict({
            'lang': Bilingual('english', 'welsh'),
            'none': None,
            'list': ['1', Bilingual('en', 'cy')],
            'dict': {'a': 'a', 'b': Bilingual('b_en', 'b_cy')}
        })
        self.assertEqual(data.english(), {'lang': 'english',
                                          'none': None,
                                          'list': ['1', 'en'],
                                          'dict': {'a': 'a', 'b': 'b_en'}})
        self.assertEqual(data.welsh(), {'lang': 'welsh',
                                        'none': None,
                                        'list': ['1', 'cy'],
                                        'dict': {'a': 'a', 'b': 'b_cy'}})

    def test_invalid_type(self):
        with self.assertRaisesRegex(ValueError, "^Unexpected type <class 'int'> for int:1$"):
            data = BilingualDict({
                'int': 1,
            })


if __name__ == '__main__':
    unittest.main()
