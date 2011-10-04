from munge.lex.lex import preserving_split
from apps.util.config import config

if config.hatted_cats:
    from munge.cats.hatted.parse import parse_category
elif config.headed_cats:
    from munge.cats.headed.parse import parse_category
else:
    from munge.cats.parse import parse_category

from munge.util.exceptions import CCGbankParseException
from munge.util.parse_utils import shift_and_check, ensure_stream_exhausted
from nodes import Node, Leaf

class CCGNodeFactory(object):
    node_class = Node
    leaf_class = Leaf

def parse_tree(tree_string, node_factory=CCGNodeFactory):
    parser = CCGParser(node_factory)
    
    toks = preserving_split(tree_string, "()<>", suppressors='<>')

    deriv = parser.read_paren(toks)
    ensure_stream_exhausted(toks, 'ccg.parse_tree')

    return deriv
    
class CCGParser(object):
    def __init__(self, node_factory=CCGNodeFactory):
        self.node_factory = node_factory
        
    def read_paren(self, toks, parent=None):
        shift_and_check( '(', toks )
        shift_and_check( '<', toks )

        node_type = toks.peek()
        if node_type == 'T':
            result = self.read_internal_node(toks, parent)
            shift_and_check( '>', toks )

            lch = self.read_paren(toks, result)
            rch = None
            if toks.peek() == '(': rch = self.read_paren(toks, result)

            result.lch, result.rch = lch, rch
        elif node_type == 'L':
            result = self.read_leaf_node(toks, parent)
            shift_and_check( '>', toks )
        else:
            raise CCGbankParseException, \
                    "Node type (T, L) expected here."

        shift_and_check( ')', toks )

        return result

    def read_leaf_node(self, toks, parent=None):
        shift_and_check( 'L', toks )

        cat_string, pos1, pos2, lex, catfix = \
                toks.next(), toks.next(), \
                toks.next(), toks.next(), toks.next()
        cat = parse_category(cat_string)

        return self.node_factory.leaf_class(cat, pos1, pos2, lex, catfix, parent)

    def read_internal_node(self, toks, parent):
        shift_and_check( 'T', toks )

        cat_string, head_index, child_count = \
                toks.next(), toks.next(), toks.next()
        cat = parse_category(cat_string)

        return self.node_factory.node_class(cat, head_index, child_count, parent)
