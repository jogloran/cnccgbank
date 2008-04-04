from munge.lex.lex import preserving_split
from munge.util.exceptions import CCGbankParseException
from munge.util.parse_utils import with_parens, shift_and_check
from nodes import Node, Leaf

def parse_tree(tree_string):
    toks = preserving_split(tree_string, "()<>", suppressors='<>')
    return read_paren(toks)

def read_paren(toks, parent=None):
    shift_and_check( '(', toks )
    shift_and_check( '<', toks )

    node_type = toks.peek()
    if node_type == 'T':
        result = read_internal_node(toks, parent)
        lch = read_paren(toks, root)
        if toks.peek() == '(': rch = read_paren(toks, root)

        result.lch, result.rch = lch, rch
    elif node_type == 'L':
        result = read_leaf_node(toks, parent)
    else:
        raise CCGbankParseException, \
                "Node type (T, L) expected here."

    shift_and_check( '>', toks )
    shift_and_check( ')', toks )

    return result

def read_leaf_node(toks, parent=None):
    shift_and_check( 'L', toks )

    cat_string, pos1, pos2, lex, catfix = \
            toks.next(), toks.next(), \
            toks.next(), toks.next(), toks.next()
    cat = parse_category(cat_string)

    return Leaf(cat, pos1, pos2, lex, catfix, parent)

def read_internal_node(toks, parent):
    shift_and_check( 'T', toks )

    cat_string, ind1, ind2 = \
            toks.next(), toks.next(), toks.next()
    cat = parse_category(cat_string)

    return Node(cat, ind1, ind2, parent)
