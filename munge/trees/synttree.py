# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.trees.pprint import pprint_with
from munge.trees.traverse import text
from apps.util.latex.table import sanitise_category

def latex_tag_for(lex):
    if lex.startswith('*'):
        return r'\PTag{%s}' % lex
    else:
        return r'\cjk{%s}' % lex
        
def process_lex_node_repr_ccg(node, compress=False, gloss_iter=None, **kwargs):
    if node.is_leaf():
        gloss = gloss_iter.next() if gloss_iter else None
        lex = latex_tag_for(node.lex)

        if gloss:
            return r"\ensuremath{\raisebox{-\baselineskip}{\shortstack{\cf{%s} \\ \glosE{%s}{%s}}}}" % (sanitise_category(str(node.cat)), lex, gloss)
        else:
            return "{\\cf{%s} %s}" % (sanitise_category(str(node.cat)), lex)
    else:
        return "\\cf{%s}" % sanitise_category(str(node.cat))

def process_lex_node_repr(node, compress=False, gloss_iter=None, **kwargs):
    if compress:
        gloss = gloss_iter.next() if gloss_iter else None
        
        lex = r'\cjk{%s}' % ' '.join(latex_tag_for(leaf) for leaf in text(node))
        if gloss:
            lex = r'\glosN{%s}{%s}' % (lex, gloss)
        
        return "\\Pos{%s} %s %s" % (
            node.tag, 
            "\\edge[roof]; " if node.count()>1 else '', 
            lex)
    if node.is_leaf():
        gloss = gloss_iter.next() if gloss_iter else None
        lex = latex_tag_for(node.lex)
        
        if gloss:
            lex = r'\glosE{%s}{%s}' % (lex, gloss)
        return "\\Pos{%s} [ .%s ]" % (node.tag, lex)
    else:
        return "\\Pos{%s}" % node.tag
        
def is_trace(tag):
    return tag == '-NONE-'

Lnode_id = 0
def process_lex_node_reprL(node, compress=False, **kwargs):
    if compress:
        lex = r'\cjk{%s}' % ' '.join(latex_tag_for(leaf) for leaf in text(node))

        return "\\Pos{%s} %s %s" % (
            node.tag,
            "\\edge[roof]; " if node.count()>1 else '',
            lex)
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
def process_lex_node_reprR(node, compress=False, gloss_iter=None, **kwargs):
    if compress:
        gloss = gloss_iter.next() if gloss_iter else None

        lex = r'\cjk{%s}' % ' '.join(latex_tag_for(leaf) for leaf in text(node))

        if gloss:
            lex = r'\glosE{%s}{%s}' % (lex, gloss)

        return "\\cf{%s} %s %s" % (
            sanitise_category(str(node.category)),
            "\\edge[roof]; " if node.count()>1 else '',
            lex)
    if node.is_leaf():
        global Rnode_id

        lex = latex_tag_for(node.lex)

        gloss = gloss_iter.next() if gloss_iter else None
        if gloss:
            lex = r'\glosE{%s}{%s}' % (lex, gloss)

        result = "\\node(r%s){\\cf{%s} %s};" % (Rnode_id, sanitise_category(str(node.category)), lex)
        Rnode_id += 1
        return result
    else:
        return "\\cf{%s}" % sanitise_category(str(node.category))

def reset_ids():
    global Lnode_id
    global Rnode_id
    Lnode_id = Rnode_id = 0
    
pprint_synttree_ccg = pprint_with(process_lex_node_repr_ccg, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)
pprint_synttree = pprint_with(process_lex_node_repr, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)
pprint_synttreeL = pprint_with(process_lex_node_reprL, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)
pprint_synttreeR = pprint_with(process_lex_node_reprR, open='[.', close=' ]', bracket_outermost=False, do_reduce=False)

def process_lex_node_yz(node, **kwargs):
    if node.is_leaf():
        return '%s c %s %s' % (str(node.cat), node.pos1, node.lex)
    else:
        if node.count() == 1:
            headedness = 's'
        elif int(node.head_index) == 0:
            headedness = 'l'
        else:
            headedness = 'r'
        
        return ' %s %s ' % (str(node.cat), headedness)

pprint_yz = pprint_with(process_lex_node_yz, open='( ', close=' ) ', bracket_outermost=False, do_reduce=False)
