import unittest
from munge.penn.parse import *

class PennParseTests(unittest.TestCase):
    def testParseSinglePennDeriv(self):
        deriv = '''
( (S 
    (NP-SBJ 
      (NP (NNP Pierre) (NNP Vinken) )
      (, ,) 
      (ADJP 
        (NP (CD 61) (NNS years) )
        (JJ old) )
      (, ,) )
    (VP (MD will) 
      (VP (VB join) 
        (NP (DT the) (NN board) )
        (PP-CLR (IN as) 
          (NP (DT a) (JJ nonexecutive) (NN director) ))
        (NP-TMP (NNP Nov.) (CD 29) )))
    (. .) ))'''
        docs = parse_tree(deriv)
        self.assertEqual(len(docs), 1)
        self.assertEqual(str(docs[0]), r'<S <NP-SBJ <NP <NNP Pierre> <NNP Vinken>> <, ,> <ADJP <NP <CD 61> <NNS years>> <JJ old>> <, ,>> <VP <MD will> <VP <VB join> <NP <DT the> <NN board>> <PP-CLR <IN as> <NP <DT a> <JJ nonexecutive> <NN director>>> <NP-TMP <NNP Nov.> <CD 29>>>> <. .>>')

    def testIgnoresWhitespace(self):
        deriv = '''

       (        (A      (B c) (D e   ) (  F  g)  

\r\r                            )

                    )'''
        docs = parse_tree(deriv)
        self.assertEqual(len(docs), 1)
        doc = docs[0]

        self.assertEqual(doc.tag, 'A') # root level tag
        self.assertEqual(doc.count(), 3) # number of children
        for (actual, expected) in zip([kid.lex for kid in doc.kids], ('c', 'e', 'g')):
            self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()
