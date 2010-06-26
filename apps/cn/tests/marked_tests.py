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
            ('(S[dcl]\NP)/NP', '((S[dcl]{_}\NP{Y}){_}/NP{Z}){_}')
        ):
            self.assertEqual(repr(label(parse_category(before))), after)

if __name__ == '__main__':
    unittest.main()