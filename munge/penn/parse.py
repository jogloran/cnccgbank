# Parses the PTB string representation of a derivation.
from munge.lex.lex import preserving_split
from munge.util.exceptions import PennParseException
from nodes import Node, Leaf

def with_parens(func, toks):
    shift_and_check( '(', toks )
    value = func(toks)
    shift_and_check( ')', toks )
    return value

def shift_and_check(tok, toks):
    next = toks.next()
    if tok != next: raise PennParseException("Expected %s, got %s" % (tok, next))

def parse_tree(tree_string):
    toks = preserving_split(tree_string, "()")
    return read_docs(toks)

def read_docs(toks):
    docs = []
    if toks.peek() == '(':
        docs.append( read_paren(toks) )
    return docs

def read_paren(toks):
    return with_parens(read_deriv, toks)

def read_deriv(toks):
    def body(toks):
        tag = toks.next()
        kids = []

        while toks.peek() != ')':
            if toks.peek() == '(':
                kids.append( read_deriv(toks) )
            else:
                lex = toks.next()

        if (not kids) and lex:
            return Leaf(tag, lex)
        else:
            return Node(tag, kids)

    return with_parens(body, toks)

