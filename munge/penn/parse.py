# Parses the PTB string representation of a derivation.
from munge.lex.lex import preserving_split
from munge.util.exceptions import PennParseException
from munge.util.parse_utils import with_parens, shift_and_check, ensure_stream_exhausted
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
            
class AugmentedPennParser(PennParser):
    def __init__(self):
        PennParser.__init__(self)
        
    def read_deriv(self, toks, parent=None):
        def body(toks):
            # HACK
            tag = toks.next()
            
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
                return A.Leaf(category, tag, lex, parent)
            else:
                ret = A.Node(category, tag, kids, parent)
                for kid in ret: kid.parent = ret
                return ret
                
        return with_parens(body, toks)

def parse_tree(tree_string, parser_class):
    penn_parser = parser_class()

    toks = preserving_split(tree_string, "(){}", suppressors="{}")

    docs = penn_parser.read_docs(toks)
    ensure_stream_exhausted(toks, 'penn.parse_tree')

    return docs