import unittest
from munge.penn.penn import Node, Leaf

class PennTests(unittest.TestCase):
    def setUp(self):
        self.n = Node('a', [Leaf('L', lex) for lex in ('b', 'c', 'd', 'e')])

    def testNodeChildIteration(self):
        kids = []
        for kid in self.n: kids.append(kid)
        self.assertEqual([kid.lex for kid in kids], ['b', 'c', 'd', 'e'])

    def testNodeRepresentation(self):
        self.assertEqual(repr(self.n), "<a <L b> <L c> <L d> <L e>>")

if __name__ == '__main__':
    unittest.main()
