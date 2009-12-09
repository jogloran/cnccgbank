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
        self.assertTrue(matches(self.tree, 'S[dcl]')) # root
        self.assertTrue(matches(self.tree, 'NP[conj]')) # internal node
        self.assertTrue(matches(self.tree, r'(S[to]\NP)/(S[b]\NP)')) # leaf
        
        self.assertFalse(matches(self.tree, 'A'))
        self.assertFalse(matches(self.tree, r'(S[to]\NP)/(S[to]\NP)'))
        self.assertFalse(matches(self.tree, 'BAR'))
        
    def testRegex(self):
        self.assertTrue(matches(self.tree, r'/\(S/S\)/+/')) # try to match (S/S)/S[dcl] 'Although'
        self.assertTrue(matches(self.tree, r'/NP\[.+\]/'))
        self.assertTrue(matches(self.tree, r'/\(S[/\\]NP\)[/\\]\(S[/\\]NP\)/'))
        
        self.assertFalse(matches(self.tree, r'/\(.+\)/\(NP/NP\)/'))
        self.assertFalse(matches(self.tree, r'/\[em\][\/].+/'))
        
    def testParent(self):
        self.assertTrue(matches(self.tree, r'S[dcl]\NP < (S[dcl]\NP)/(S[pss]\NP)'))
        self.assertTrue(matches(self.tree, r'NP[nb]/N < NP[nb]/N'))
        self.assertTrue(matches(self.tree, r'NP[nb]/N < (NP[nb]/N)\NP'))
        self.assertTrue(matches(self.tree, r'S[dcl] < "."')) # literal notation
        
        # dominates but not immediately dominates (leaf 'appear', 'in')
        self.assertFalse(matches(self.tree, r'S[dcl]\NP < ((S\NP)\(S\NP))/NP')) 
        # 'NP/NP' is the parent of 'S[adj]\NP' but not vice versa
        self.assertFalse(matches(self.tree, r'S[adj]\NP < NP/NP'))
        self.assertFalse(matches(self.tree, r'A < S[dcl]')) # Nowhere in tree
        
    def testDominates(self):
        self.assertTrue(matches(self.tree, r'S[dcl]\NP << ((S\NP)\(S\NP))/NP'))
        self.assertTrue(matches(self.tree, r'S[dcl] << "."'))
        self.assertTrue(matches(self.tree, r'S[dcl] << (NP/NP)\(S[adj]\NP)'))
        
        self.assertFalse(matches(self.tree, r'(NP[nb]/N)\NP << S[dcl]'))
        self.assertFalse(matches(self.tree, r'S[adj]\NP << NP/NP'))
        self.assertFalse(matches(self.tree, r'A << S[dcl]'))
        
    def testIsSiblingOf(self):
        self.assertTrue(matches(self.tree, r'((S\NP)\(S\NP))/NP $ NP'))
        self.assertFalse(matches(self.tree, r'((S\NP)\(S\NP))/NP $ (S[b]\NP)/NP'))
        
        self.assertTrue(matches(self.tree, r'NP $ NP[conj]'))
        self.assertTrue(matches(self.tree, r'NP[conj] $ NP'))
        self.assertFalse(matches(self.tree, r'S[dcl] $ NP'))
        
        self.assertFalse(matches(self.tree, r'A $ A'))
        self.assertFalse(matches(self.tree, r'S[dcl] $ S[dcl]'))
        
    def testIsLeftChildOf(self):
        self.assertTrue(matches(self.tree, r'NP <1 NP[nb]/N'))
        self.assertFalse(matches(self.tree, r'NP <2 NP[nb]/N'))
        
        self.assertFalse(matches(self.tree, r'A <1 B'))
        
    def testIsRightChildOf(self):
        self.assertTrue(matches(self.tree, r'S[to]\NP <2 S[b]\NP'))
        self.assertFalse(matches(self.tree, r'S[to]\NP <1 S[b]\NP'))
        
        # NP -> N is a unary conversion, so has no right child
        # I am trying to address subtree 'preliminary findings'
        self.assertFalse(matches(self.tree, r'{NP $ { (S/S)/S[dcl] $ S[dcl]\NP } } <2 {N <1 N/N <2 N}'))
        
        self.assertFalse(matches(self.tree, r'A <2 B'))

    def testAlternation(self):
        self.assertTrue(matches(self.tree, r'{((S\NP)\(S\NP))\NP $ NP} > (S\NP)\(S\NP) | < T'))
        self.assertTrue(matches(self.tree, r'{((S\NP)\(S\NP))\NP $ NP} < T | > (S\NP)\(S\NP)'))
        self.assertFalse(matches(self.tree, r'{((S\NP)\(S\NP))\NP $ NP} < A | > B | $ C'))
        self.assertTrue(matches(self.tree, r'{((S\NP)\(S\NP))\NP $ NP} < A | > (S\NP)\(S\NP) | $ C'))
        
if __name__ == '__main__':
    unittest.main()
