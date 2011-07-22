from munge.trees.pprint import pprint_with

def process_lex_node_repr(node, compress=False):
    if compress:
        return "%s \\edge[roof]; \\cjk{%s}" % (node.tag, ' '.join(node.text()))
    if node.is_leaf():
        return "%s \\cjk{%s}" % (node.tag, node.lex)
    else:
        return "%s" % node.tag
        
pprint_synttree = pprint_with(process_lex_node_repr, open='[.', close=' ]', bracket_outermost=False)
pprint_synttree_top = pprint_with(process_lex_node_repr, open='[.', close=' ]', bracket_outermost=False, detail_level=2)