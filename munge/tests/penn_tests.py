import unittest
from munge.penn.nodes import Node, Leaf
from munge.penn.parse import parse_tree
from munge.vis.dot import *

import os

class PennTests(unittest.TestCase):
    def setUp(self):
        self.n = Node('a', [Leaf('L', lex) for lex in ('b', 'c', 'd', 'e')])
        self.from_penn= '''( (S 
		    (NP-SBJ-1 
		      (NP (NNP Ratners) (NNP Group) (NNP PLC) (POS 's) )
		      (NNP U.S.) (NN subsidiary) )
		    (VP (VBZ has) 
		      (VP (VBN agreed) 
		        (S 
		          (NP-SBJ (-NONE- *-1) )
		          (VP (TO to) 
		            (VP (VB acquire) 
		              (NP (NN jewelry) (NN retailer) 
		                (NP (NNP Weisfield) (POS 's) )
		                (NNP Inc.) )
		              (PP-CLR (IN for) 
		                (NP 
		                  (NP 
		                    (NP ($ $) (CD 50) (-NONE- *U*) )
		                    (NP-ADV (DT a) (NN share) ))
		                  (, ,) (CC or) 
		                  (NP 
		                    (QP (IN about) ($ $) (CD 55) (CD million) )
		                    (-NONE- *U*) ))))))))
		    (. .) ))
        '''

    def testNodeChildIteration(self):
        kids = []
        for kid in self.n: kids.append(kid)
        self.assertEqual([kid.lex for kid in kids], ['b', 'c', 'd', 'e'])

    def testNodeRepresentation(self):
        self.assertEqual(repr(self.n), "(a (L b) (L c) (L d) (L e))")

    def testWriteDerivation(self):
        trees = parse_tree(self.from_penn)
        self.assertEqual(len(trees), 1)
        tree = trees[0]

        write_graph(tree, 'penn_deriv.dot')
        self.assert_(os.path.exists('penn_deriv.dot'))

if __name__ == '__main__':
    unittest.main()
