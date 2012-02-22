# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import os
import unittest
from munge.cats.nodes import *
from munge.cats.parse import *
from munge.vis.dot import *

class CatTests(unittest.TestCase):
    def setUp(self):
        self.lch = AtomicCategory('S')
        self.rch = AtomicCategory('NP')
        self.n = ComplexCategory(self.lch, BACKWARD, self.rch)

        self.n2 = parse_category('(S\\NP)/(S\\NP)')

    def testWriteCategoryTree(self):
        write_graph(self.n2, 'cat.dot')
        self.assert_(os.path.exists('cat.dot'))

    def testModedCategoryRepr(self):
        cat = ComplexCategory(
                ComplexCategory( AtomicCategory('S'), BACKWARD, AtomicCategory('NP', ['b']), NULL ),
                FORWARD,
                ComplexCategory( AtomicCategory('S', ['c']), FORWARD, AtomicCategory('NP'), COMP ),
                ALL, ['feat'])

        self.assertEqual(repr(cat), r'(S\-NP[b])/.(S[c]/@NP)[feat]')

    def tearDown(self):
        if os.path.exists('cat.dot'):
            os.remove('cat.dot')
