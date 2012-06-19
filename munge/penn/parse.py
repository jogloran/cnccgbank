# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

# Parses the PTB string representation of a derivation.
from munge.lex.lex import preserving_split
from munge.util.parse_utils import with_parens, shift_and_check, ensure_stream_exhausted

from munge.util.config import config

if config.headed_cats:
    from munge.cats.headed.parse import parse_category
else:
    from munge.cats.parse import parse_category
    
import munge.penn.nodes as N
import munge.penn.aug_nodes as A
    
class PennParser(object):
    def read_docs(self, toks):
        docs = []
        while toks.peek() == '(':
            docs.append( self.read_paren(toks) )
        return docs

    def read_paren(self, toks):
        return with_parens(self.read_deriv, toks)

    def read_deriv(self, toks, parent=None):
        def body(toks):
            tag = toks.next()
            lex = None
        
            kids = []

            while toks.peek() != ')':
                if toks.peek() == '(':
                    kids.append( self.read_deriv(toks) )
                else:
                    lex = toks.next()

            if (not kids) and lex:
                return N.Leaf(tag, lex, parent)
            else:
                ret = N.Node(tag, kids, parent)
                for kid in ret: kid.parent = ret
                return ret
                
        return with_parens(body, toks)

class CategoryPennParser(PennParser):
    def __init__(self):
        PennParser.__init__(self)

    def read_deriv(self, toks, parent=None):
        def body(toks):
            # HACK
            tag = "_"
            head_index = 0 # head_index must be [01]; required by script convert_auto

            category = toks.next().replace('{', '(').replace('}', ')')
            kids = []

            lex = None
            while toks.peek() != ')':
                if toks.peek() == '(':
                    kids.append( self.read_deriv(toks) )
                else:
                    lex = toks.next()

            if (not kids) and lex:
                return A.Leaf(tag, lex, category, parent)
            else:
                ret = A.Node(tag, kids, category, parent, head_index)
                for kid in ret: kid.parent = ret
                return ret
                
        return with_parens(body, toks)
        
class CAugmentedPennParser(PennParser):
    def read_docs(self, toks):
        print 'toks', toks
        result = augpenn_parse(toks, "(){}<>", " \t\r\n", "{}")
        print 'result',result
        toks.clear()
        return result
            
class PythonAugmentedPennParser(PennParser):
    def __init__(self):
        PennParser.__init__(self)
        
    def read_deriv(self, toks, parent=None):
        def body(toks):
            # HACK
            tag = toks.next()
            
            head_index = None
            if toks.peek() == '<':
                toks.next()
                head_index = int(toks.next())
                shift_and_check( '>', toks )
            
            category = None
            if toks.peek() == '{':        
                toks.next()
                category = parse_category(toks.next())
                shift_and_check( '}', toks )
        
            kids = []

            lex = None
            while toks.peek() != ')':
                if toks.peek() == '(':
                    kids.append( self.read_deriv(toks) )
                else:
                    lex = toks.next()

            if (not kids) and lex:
                return A.Leaf(tag, lex, category, parent)
            else:
                ret = A.Node(tag, kids, category, parent, head_index)
                for kid in ret: kid.parent = ret
                return ret
                
        return with_parens(body, toks)
        
try:
    from pressplit2 import augpenn_parse
    AugmentedPennParser = CAugmentedPennParser
except ImportError:
    AugmentedPennParser = PythonAugmentedPennParser
    
def parse_tree(tree_string, _, split_chars="(){}<>", suppressors="{}"):
    return augpenn_parse(tree_string, "(){}<>", " \t\r\n", "{}")

# def parse_tree(tree_string, parser_class, split_chars="(){}<>", suppressors="{}"):
#     penn_parser = parser_class()
# 
#     toks = preserving_split(tree_string, split_chars, suppressors=suppressors)
# 
#     docs = penn_parser.read_docs(toks)
#     ensure_stream_exhausted(toks, 'penn.parse_tree')
# 
#     return docs
