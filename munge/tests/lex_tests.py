# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import unittest
from munge.lex.lex import preserving_split

class LexTests(unittest.TestCase):
    def setUp(self):
        pass

    def testAdjacentSplitters(self):
        result = [tok for tok in preserving_split(r'a.b.cd.ef..g', '.')]
        self.assertEqual(result, r'a . b . cd . ef . . g'.split(" "))

    def testPeek(self):
        stream = preserving_split('abc/def.ghi', './')
        for expected_tok in ('abc', '/', 'def', '.', 'ghi'):
            self.assertEqual(stream.peek(), expected_tok)
            stream.next()

    def testEmptyPeek(self):
        stream = preserving_split('', '@#$')
        self.assertRaises(StopIteration, stream.next)
        self.failIf(stream.peek()) # peek must yield None

    def testPreserves(self):
        s = r'<a href="index.html">Text</a>'
        result = [tok for tok in preserving_split(s, r'<>="/')]
        self.assertEqual(result, r'< a href = " index.html " > Text < / a >'.split(" "))

    def testPennSplit(self):
        s = ''' 
( (S 
    (NP-SBJ (NNP Mr.) (NNP Vinken) )
    (VP (VBZ is) 
      (NP-PRD 
        (NP (NN chairman) )
        (PP (IN of) 
          (NP 
            (NP (NNP Elsevier) (NNP N.V.) )
            (, ,) 
            (NP (DT the) (NNP Dutch) (VBG publishing) (NN group) )))))
    (. .) ))'''
        
        result = [tok for tok in preserving_split(s, r'()')]
        self.assertEqual(result, '''( ( S ( NP-SBJ ( NNP Mr. ) ( NNP Vinken ) ) ( VP ( VBZ is ) ( NP-PRD ( NP ( NN chairman ) ) ( PP ( IN of ) ( NP ( NP ( NNP Elsevier ) ( NNP N.V. ) ) ( , , ) ( NP ( DT the ) ( NNP Dutch ) ( VBG publishing ) ( NN group ) ) ) ) ) ) ( . . ) ) )'''.split(" "))

    def testOnlySplitOnWhitespace(self):
        s = r'<a href="index.html">Text</a>'
        result = [tok for tok in preserving_split(s, r'@#$%')]
        self.assertEqual(result, r'<a href="index.html">Text</a>'.split(" "))

    def testSplitOnNothing(self):
        s = r'<a href="index.html">Text</a>'
        result = [tok for tok in preserving_split(s, '', skip_chars='')]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], s)

    def testEmptyInput(self):
        result = [tok for tok in preserving_split('', '')]
        self.failIf(result)

if __name__ == '__main__':
    unittest.main()
