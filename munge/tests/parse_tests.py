import unittest
from munge.penn.parse import preserving_split

class ParseTests(unittest.TestCase):
    def testNoSuppressors(self):
        s = r'(<L a.b c.d e>)'
        stream = preserving_split(s, '()<>.')
        self.assertEqual([tok for tok in stream], (r'( < L a . b c . d e > )'.split(' ')))

    def testSuppressors(self):
        s = r'(<L a.b c.d e>)'
        stream = preserving_split(s, '()<>.', suppressors='<>')
        self.assertEqual([tok for tok in stream], ['(', '<', 'L', 'a.b', 'c.d', 'e', '>', ')'])

if __name__ == '__main__':
    unittest.main()
