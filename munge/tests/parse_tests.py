# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

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
