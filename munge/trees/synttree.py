from munge.trees.pprint import pprint_with
from munge.trees.traverse import text

def process_lex_node_repr(node, compress=False):
    if compress:
        return "%s %s \\cjk{%s}" % (node.tag, "\\edge[roof]; " if node.count()>1 else '', ' '.join(text(node)))
    if node.is_leaf():
        return "%s \\cjk{%s}" % (node.tag, node.lex)
    else:
        return "%s" % node.tag
        
pprint_synttree = pprint_with(process_lex_node_repr, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)
pprint_synttree_top = pprint_with(process_lex_node_repr, open='[.', close=' ]', bracket_outermost=False, detail_level=1, do_reduce=False)