# Parses the PTB string representation of a derivation.
from munge.lex.lex import preserving_split
from munge.util.exceptions import PennParseException
from munge.util.parse_utils import with_parens, shift_and_check, ensure_stream_exhausted
from nodes import Node, Leaf

def parse_tree(tree_string):
    toks = preserving_split(tree_string, "()")

    docs = read_docs(toks)
    ensure_stream_exhausted(toks, 'penn.parse_tree')

    return docs

def read_docs(toks):
    docs = []
    while toks.peek() == '(':
        docs.append( read_paren(toks) )
    return docs

def read_paren(toks):
    return with_parens(read_deriv, toks)

def read_deriv(toks, parent=None):
    def body(toks):
        tag = toks.next()
        kids = []

        while toks.peek() != ')':
            if toks.peek() == '(':
                kids.append( read_deriv(toks) )
            else:
                lex = toks.next()

        if (not kids) and lex:
            return Leaf(tag, lex, parent)
        else:
            ret = Node(tag, kids, parent)
            for kid in ret: kid.parent = ret
            return ret

    return with_parens(body, toks)
