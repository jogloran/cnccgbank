import unittest
from munge.lex.lex import preserving_split

class TestLex(unittest.TestCase):
    def setUp(self):
        pass

    def testAdjacentSplitters(self):
        result = []
        for tok in preserving_split(r'a.b.cd.ef..g', '.'):
            result.append(tok)
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
        result = []
        for tok in preserving_split(s, r'<>="/'):
            result.append(tok)
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
        
        result = []
        for tok in preserving_split(s, r'()'):
            result.append(tok)

        self.assertEqual(result, '''( ( S ( NP-SBJ ( NNP Mr. ) ( NNP Vinken ) ) ( VP ( VBZ is ) ( NP-PRD ( NP ( NN chairman ) ) ( PP ( IN of ) ( NP ( NP ( NNP Elsevier ) ( NNP N.V. ) ) ( , , ) ( NP ( DT the ) ( NNP Dutch ) ( VBG publishing ) ( NN group ) ) ) ) ) ) ( . . ) ) )'''.split(" "))

    def testOnlySplitOnWhitespace(self):
        s = r'<a href="index.html">Text</a>'
        result = []
        for tok in preserving_split(s, r'@#$%'):
            result.append(tok)
        self.assertEqual(result, r'<a href="index.html">Text</a>'.split(" "))

    def testSplitOnNothing(self):
        s = r'<a href="index.html">Text</a>'
        result = []
        for tok in preserving_split(s, '', skip_chars=''):
            result.append(tok)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], s)

    def testEmptyInput(self):
        result = []
        for tok in preserving_split('', ''): result.append(tok)
        self.failIf(result)

if __name__ == '__main__':
    unittest.main()
