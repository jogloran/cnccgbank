# Parses the PTB string representation of a derivation.
from munge.lex.lex import preserving_split
from munge.util.exceptions import PennParseException
from munge.util.parse_utils import with_parens, shift_and_check, ensure_stream_exhausted
import nodes as N
import aug_nodes as A

class PennNodeFactory(object):
    node_class = N.Node
    leaf_class = N.Leaf
    
class AugmentedPennNodeFactory(object):
    node_class = A.Node
    leaf_class = A.Leaf

def parse_tree(tree_string, node_factory=PennNodeFactory):
    penn_parser = PennParser(node_factory)
    
    toks = preserving_split(tree_string, "()")

    docs = penn_parser.read_docs(toks)
    ensure_stream_exhausted(toks, 'penn.parse_tree')

    return docs
    
class PennParser(object):
    def __init__(self, node_factory=PennNodeFactory):
        self.node_factory = node_factory
        
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
            kids = []

            while toks.peek() != ')':
                if toks.peek() == '(':
                    kids.append( self.read_deriv(toks) )
                else:
                    lex = toks.next()

            if (not kids) and lex:
                return self.node_factory.leaf_class(tag, lex, parent)
            else:
                ret = self.node_factory.node_class(tag, kids, parent)
                for kid in ret: kid.parent = ret
                return ret

        return with_parens(body, toks)