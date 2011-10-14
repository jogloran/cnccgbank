from munge.trees.pprint import pprint_with
from munge.trees.traverse import text
from apps.util.latex.table import sanitise_category

def latex_tag_for(lex):
    if lex.startswith('*'):
        return r'\PTag{%s}' % lex
    else:
        return r'\cjk{%s}' % lex
        
def process_lex_node_repr(node, compress=False):
    if compress:
        return "\\Pos{%s} %s \\cjk{%s}" % (node.tag, "\\edge[roof]; " if node.count()>1 else '', ' '.join(text(node)))
    if node.is_leaf():
        return "{\\Pos{%s} %s}" % (node.tag, latex_tag_for(node.lex))
    else:
        return "\\Pos{%s}" % node.tag
        
def is_trace(tag):
    return tag == '-NONE-'

Lnode_id = 0
def process_lex_node_reprL(node, compress=False):
    if compress:
        return "\\Pos{%s} %s \\cjk{%s}" % (node.tag, "\\edge[roof]; " if node.count()>1 else '', ' '.join(text(node)))
    if node.is_leaf():
        if is_trace(node.tag):
            result = "\\node{\\Pos{%s} %s};" % (node.tag, latex_tag_for(node.lex))
        else:
            global Lnode_id
            result = "\\node(l%s){\\Pos{%s} %s};" % (Lnode_id, node.tag, latex_tag_for(node.lex))
            Lnode_id += 1
        return result
    else:
        return "\\Pos{%s}" % node.tag
        
Rnode_id = 0
def process_lex_node_reprR(node, compress=False):
    if compress:
        return "\\cf{%s} %s \\cjk{%s}" % (sanitise_category(str(node.category)), "\\edge[roof]; " if node.count()>1 else '', ' '.join(text(node)))
    if node.is_leaf():
        global Rnode_id
        result = "\\node(r%s){\\cf{%s} %s};" % (Rnode_id, sanitise_category(str(node.category)), latex_tag_for(node.lex))
        Rnode_id += 1
        return result
    else:
        return "\\cf{%s}" % sanitise_category(str(node.category))

def reset_ids():
    global Lnode_id
    global Rnode_id
    Lnode_id = Rnode_id = 0
    
pprint_synttree = pprint_with(process_lex_node_repr, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)
pprint_synttreeL = pprint_with(process_lex_node_reprL, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)
pprint_synttreeR = pprint_with(process_lex_node_reprR, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)