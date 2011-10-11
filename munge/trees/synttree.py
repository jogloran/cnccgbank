from munge.trees.pprint import pprint_with
from munge.trees.traverse import text
from apps.util.latex.table import sanitise_category

def process_lex_node_repr(node, compress=False):
    if compress:
        return "\\Pos{%s} %s \\cjk{%s}" % (node.tag, "\\edge[roof]; " if node.count()>1 else '', ' '.join(text(node)))
    if node.is_leaf():
        return "{\\Pos{%s} \\cjk{%s}}" % (node.tag, node.lex)
    else:
        return "\\Pos{%s}" % node.tag

Lnode_id = 0
def process_lex_node_reprL(node, compress=False):
    if compress:
        return "%s %s \\cjk{%s}" % (node.tag, "\\edge[roof]; " if node.count()>1 else '', ' '.join(text(node)))
    if node.is_leaf():
        global Lnode_id
        result = "%s \\node(l%s){\\cjk{%s}};" % (node.tag, Lnode_id, node.lex)
        Lnode_id += 1
        return result
    else:
        return "%s" % node.tag
        
Rnode_id = 0
def process_lex_node_reprR(node, compress=False):
    if compress:
        return "\\cf{%s} %s \\cjk{%s}" % (sanitise_category(str(node.category)), "\\edge[roof]; " if node.count()>1 else '', ' '.join(text(node)))
    if node.is_leaf():
        global Rnode_id
        result = "\\node(r%s){\\cf{%s} \\cjk{%s}};" % (Rnode_id, sanitise_category(str(node.category)), node.lex)
        Rnode_id += 1
        return result
    else:
        return "\\cf{%s}" % sanitise_category(str(node.category))
        
pprint_synttree = pprint_with(process_lex_node_repr, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)
pprint_synttreeL = pprint_with(process_lex_node_reprL, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)
pprint_synttreeR = pprint_with(process_lex_node_reprR, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)