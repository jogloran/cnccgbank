import os
import unittest
from munge.ccg.nodes import Node, Leaf
from munge.ccg.parse import parse_tree
from munge.cats.nodes import AtomicCategory
from munge.vis.dot import *

class CCGTests(unittest.TestCase):
    def setUp(self):
        self.lch = Leaf(AtomicCategory('Ldummycat1'), 'Lpos1', 'Lpos2', 'Llex', 'Lcatfix') 
        self.rch = Leaf(AtomicCategory('Rdummycat1'), 'Rpos1', 'Rpos2', 'Rlex', 'Rcatfix') 
        self.n = Node(AtomicCategory('dummycat'), 'ind1', 'ind2', None, self.lch, self.rch)
        
        self.from_ccgbank = '''(<T NP 0 2> (<T NP 0 2> (<T NP 0 2> (<T NP 0 2> (<T NP 0 2> (<T NP 0 1> (<T N 0 2> (<L N/N[num] $ $ $ N/N[num]_34>) (<T N[num] 1 2> (<L N/N CD CD 117 N_43/N_43>) (<L N[num] CD CD million N[num]>) ) ) ) (<T NP\NP 0 2> (<L (NP\NP)/NP IN IN of (NP_52\NP_52)/NP_53>) (<T NP 0 2> (<T NP 0 1> (<T N 1 2> (<L N/N NN NN revenue N_62/N_62>) (<L N NNS NNS bonds N>) ) ) (<T NP\NP 0 2> (<L (NP\NP)/NP IN IN for (NP_71\NP_71)/NP_72>) (<T NP 0 1> (<T N 1 2> (<L N/N NNP NNP Hahnemann N_81/N_81>) (<L N NNP NNP University N>) ) ) ) ) ) ) (<T NP[conj] 1 2> (<L , , , , ,>) (<T NP 0 1> (<T N 0 2> (<L N NNP NNP Series N>) (<L N\N CD CD 1989 N_91\N_91>) ) ) ) ) (<L , , , , ,>) ) (<T NP\NP 0 2> (<L (NP\NP)/NP IN IN via (NP_104\NP_104)/NP_105>) (<T NP 1 2> (<L NP[nb]/N DT DT a NP[nb]_126/N_126>) (<T N 1 2> (<L N/N NNP NNP Merrill N_121/N_121>) (<T N 1 2> (<L N/N NNP NNP Lynch N_114/N_114>) (<L N NN NN group N>) ) ) ) ) ) (<L . . . . .>) )'''

    def testParseInverseParse(self):
        deriv_string = '(<T dummycat ind1 ind2> (<L Ldummycat1 Lpos1 Lpos2 Llex Lcatfix>) (<L Rdummycat1 Rpos1 Rpos2 Rlex Rcatfix>) )'
        self.assertEqual(repr(self.n), deriv_string)
        self.assertEqual(self.n, parse_tree(deriv_string))

    def testWriteDerivation(self):
        tree = parse_tree(self.from_ccgbank)
        write_graph(tree, 'ccg_deriv.dot')
        self.assert_(os.path.exists('ccg_deriv.dot'))

        # TODO: Had problems with 01:0(1), need to investigate

if __name__ == '__main__':
    unittest.main()
