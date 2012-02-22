# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import unittest

from apps.cn.mkmarked import *
from munge.cats.headed.parse import parse_category

class MarkedTests(unittest.TestCase):
    def testMarked(self):
        for (before, after) in (
            ('N/N', '(N{Y}/N{Y}){_}'),
            ('NP/N', '(NP{Y}/N{Y}){_}'),
            (r'S[q]\S[dcl]', '(S[q]{Y}\S[dcl]{Y}){_}'),
            (r'(S\NP)/(S\NP)', '((S{Y}\NP{Z}){Y}/(S{Y}\NP{Z}){Y}){_}'),
            ('X', 'X{_}'),
            ('(S[dcl]\NP)/NP', '((S[dcl]{_}\NP{Y}){_}/NP{Z}){_}'),
            (',', ',{_}'),
            ('(S[dcl]\NP)/(S[dcl]\NP)','((S[dcl]{_}\NP{Y}){_}/(S[dcl]{Z}\NP{Y}){Z}){_}'),
        ):
            self.assertEqual(repr(label(parse_category(before))), after)

if __name__ == '__main__':
    unittest.main()