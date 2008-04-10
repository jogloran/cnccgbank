import os
import unittest
from munge.cats.repr import *
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
