import unittest, os
from munge.proc.tgrep.tgrep import *
from munge.ccg.io import CCGbankReader

class TgrepTests(unittest.TestCase):
    def setUp(self):
        self.assert_(os.path.exists('munge/tests/wsj_0003.auto'))
        self.tree = CCGbankReader('munge/tests/wsj_0003.auto')[ 4 ].derivation
        
        initialise()
        
    def testCorrectTreeLoaded(self):
        self.assertEquals(self.tree.text(), "Although preliminary findings were reported more than a "
                                            "year ago , the latest results appear in today 's New England "
                                            "Journal of Medicine , a forum likely to bring new attention "
                                            "to the problem .".split())
                                            
    def testAtom(self):
        self.assertTrue(tgrep(self.tree, 'S[dcl]')) # root
        self.assertTrue(tgrep(self.tree, 'NP[conj]')) # internal node
        self.assertTrue(tgrep(self.tree, r'(S[to]\.NP)/.(S[b]\.NP)')) # leaf
        
        self.assertFalse(tgrep(self.tree, 'A'))
        self.assertFalse(tgrep(self.tree, r'(S[to]\.NP)/.(S[to]\.NP)'))
        self.assertFalse(tgrep(self.tree, 'BAR'))
        
    def testRegex(self):
        self.assertTrue(tgrep(self.tree, r'/\(S/.S\)/.+/')) # try to match (S/.S)/.S[dcl] 'Although'
        self.assertTrue(tgrep(self.tree, r'/NP\[.+\]/'))
        self.assertTrue(tgrep(self.tree, r'/\(S[/\\].NP\)[/\\].\(S[/\\].NP\)/'))
        
        self.assertFalse(tgrep(self.tree, r'/\(.+\)/\(NP/.NP\)/'))
        self.assertFalse(tgrep(self.tree, r'/.\[em\][\/].+/'))
        
    def testParent(self):
        self.assertTrue(tgrep(self.tree, r'S[dcl]\.NP < (S[dcl]\.NP)/.(S[pss]\.NP)'))
        self.assertTrue(tgrep(self.tree, r'NP[nb]/.N < NP[nb]/.N'))
        self.assertTrue(tgrep(self.tree, r'NP[nb]/.N < (NP[nb]/.N)\.NP'))
        self.assertTrue(tgrep(self.tree, r'S[dcl] < "."')) # literal notation
        
        # dominates but not immediately dominates (leaf 'appear', 'in')
        self.assertFalse(tgrep(self.tree, r'S[dcl]\.NP < ((S\.NP)\.(S\.NP))/.NP')) 
        # 'NP/.NP' is the parent of 'S[adj]\.NP' but not vice versa
        self.assertFalse(tgrep(self.tree, r'S[adj]\.NP < NP/.NP'))
        self.assertFalse(tgrep(self.tree, r'A < S[dcl]')) # Nowhere in tree
        
    def testDominates(self):
        self.assertTrue(tgrep(self.tree, r'S[dcl]\.NP << ((S\.NP)\.(S\.NP))/.NP'))
        self.assertTrue(tgrep(self.tree, r'S[dcl] << "."'))
        self.assertTrue(tgrep(self.tree, r'S[dcl] << (NP/.NP)\.(S[adj]\.NP)'))
        
        self.assertFalse(tgrep(self.tree, r'(NP[nb]/.N)\.NP << S[dcl]'))
        self.assertFalse(tgrep(self.tree, r'S[adj]\.NP << NP/.NP'))
        self.assertFalse(tgrep(self.tree, r'A << S[dcl]'))
        
    def testIsSiblingOf(self):
        self.assertTrue(tgrep(self.tree, r'((S\.NP)\.(S\.NP))/.NP $ NP'))
        self.assertFalse(tgrep(self.tree, r'((S\.NP)\.(S\.NP))/.NP $ (S[b]\.NP)/.NP'))
        
        self.assertTrue(tgrep(self.tree, r'NP $ NP[conj]'))
        self.assertTrue(tgrep(self.tree, r'NP[conj] $ NP'))
        self.assertFalse(tgrep(self.tree, r'S[dcl] $ NP'))
        
        self.assertFalse(tgrep(self.tree, r'A $ A'))
        self.assertFalse(tgrep(self.tree, r'S[dcl] $ S[dcl]'))
        
    def testIsLeftChildOf(self):
        self.assertTrue(tgrep(self.tree, r'NP <1 NP[nb]/.N'))
        self.assertFalse(tgrep(self.tree, r'NP <2 NP[nb]/.N'))
        
        self.assertFalse(tgrep(self.tree, r'A <1 B'))
        
    def testIsRightChildOf(self):
        self.assertTrue(tgrep(self.tree, r'S[to]\.NP <2 S[b]\.NP'))
        self.assertFalse(tgrep(self.tree, r'S[to]\.NP <1 S[b]\.NP'))
        
        # NP -> N is a unary conversion, so has no right child
        # I am trying to address subtree 'preliminary findings'
        self.assertFalse(tgrep(self.tree, r'{NP $ { (S/.S)/.S[dcl] $ S[dcl]\.NP } } <2 {N <1 N/.N <2 N}'))
        
        self.assertFalse(tgrep(self.tree, r'A <2 B'))
        
if __name__ == '__main__':
    unittest.main()