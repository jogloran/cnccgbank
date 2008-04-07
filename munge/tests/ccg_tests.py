import unittest
from munge.ccg.nodes import Node, Leaf
from munge.ccg.parse import parse_tree
from munge.cats.repr import AtomicCategory

class CCGTests(unittest.TestCase):
    def setUp(self):
        self.lch = Leaf(AtomicCategory('Ldummy-cat1'), 'Lpos1', 'Lpos2', 'Llex', 'Lcatfix') 
        self.rch = Leaf(AtomicCategory('Rdummy-cat1'), 'Rpos1', 'Rpos2', 'Rlex', 'Rcatfix') 
        self.n = Node(AtomicCategory('dummy-cat'), 'ind1', 'ind2', None, self.lch, self.rch)

    def testParseInverseParse(self):
        deriv_string = '(<T dummy-cat ind1 ind2> (<L Ldummy-cat1 Lpos1 Lpos2 Llex Lcatfix>) (<L Rdummy-cat1 Rpos1 Rpos2 Rlex Rcatfix>))'
        self.assertEqual(repr(self.n), deriv_string)
        self.assertEqual(self.n, parse_tree(deriv_string))

if __name__ == '__main__':
    unittest.main()
