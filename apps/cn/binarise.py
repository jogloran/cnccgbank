from __future__ import with_statement

from munge.trees.traverse import nodes
from munge.penn.io import parse_tree
from apps.cn.output import OutputDerivation
from apps.cn.fix_utils import *

from echo import *

# 
# import munge.penn.aug_nodes as A
# def Node(tag, kids, parent=None):
#     return A.Node(None, tag, kids, parent)
# def Leaf(tag, lex, parent=None):
#     return A.Leaf(none, tag, lex, parent)
#     
from munge.penn.nodes import Leaf, Node
from munge.trees.pprint import pprint

from munge.proc.filter import Filter
import sys, re, os

from apps.identify_lrhca import *

#@echo
def label_adjunction(node, inherit_tag=False, without_labelling=False, inside_np_internal_structure=False):
    kid_tag = node.tag if inherit_tag else re.sub(r':.+$', '', node.tag)

    if not without_labelling:
        kids = map(lambda node: label_node(node, inside_np_internal_structure=inside_np_internal_structure), node.kids)
    else:
        kids = node.kids
        
    last_kid, second_last_kid = kids.pop(), kids.pop()

    cur = Node(kid_tag, [second_last_kid, last_kid])

    while kids:
        kid = kids.pop()
        cur = Node(kid_tag, [kid, cur])
 
    cur.tag = node.tag
    return cur
    
#@echo
def label_np_internal_structure(node, inherit_tag=False):
    if (node.kids[-1].tag.endswith(':&') 
        # prevent movement when we have an NP with only two children NN ETC
        and node.count() > 2):
        
        etc = node.kids.pop()
        kid_tag = node.tag if inherit_tag else re.sub(r':.+$', '', node.tag)
        
        old_tag = node.tag
        node.tag = kid_tag
        
        return Node(old_tag, [ label_np_internal_structure(node), etc ])
    else:
        return label_adjunction(node, inside_np_internal_structure=True)
    
@echo
def label_coordination(node, inside_np_internal_structure=False):
    def label_nonconjunctions(kid):
        if kid.tag not in ('CC', 'PU'): 
            return label_node(kid, inside_np_internal_structure=inside_np_internal_structure)
        else: return kid
    
    kids = map(label_nonconjunctions, node.kids)
    return label_adjunction(Node(node.tag, kids), inside_np_internal_structure=inside_np_internal_structure, without_labelling=True)

#@echo
def label_head_initial(node, inherit_tag=False):
    kid_tag = node.tag if inherit_tag else re.sub(r':.+$', '', node.tag)
    
    kids = map(label_node, node.kids)[::-1]
    first_kid, second_kid = kids.pop(), kids.pop()

    cur = Node(kid_tag, [first_kid, second_kid])

    while kids:
        kid = kids.pop()
        cur = Node(node.tag, [cur, kid])
    
    cur.tag = node.tag
    return cur

#@echo
def label_head_final(node):
    return label_adjunction(node)
    
#@echo
def is_left_punct_absorption(l):
    return l.is_leaf() and l.tag == 'PU'

#@echo
def label_predication(node, inherit_tag=False):
    kids = map(label_node, node.kids)
    last_kid, second_last_kid = kids.pop(), kids.pop()
    
    kid_tag = node.tag if inherit_tag else re.sub(r':.+$', '', node.tag)

    # TODO: think of a better and more general way of doing this
    # this is to stop what happens in 2:4(2) with PU. what is actually happening?
    if is_left_punct_absorption(second_last_kid):
        initial_tag = 'VP'
    else:
        initial_tag = kid_tag

    cur = Node(initial_tag, [second_last_kid, last_kid])

    while kids:
        kid = kids.pop()
        cur = Node(kid_tag, [kid, cur])

    cur.tag = node.tag # restore the full tag at the topmost level
    
    return cur
    
#@echo
def label_root(node):
    final_punctuation_stk = []
    
    if all(kid.tag.startswith('PU') for kid in node):
        # Weird derivation (5:0(21)):
        # ((FRAG (PU --) (PU --) (PU --) (PU --) (PU --) (PU -)))
        return label_adjunction(node)
    
    while (not node.is_leaf()) and node.kids[-1].tag.startswith('PU'):
        final_punctuation_stk.append( node.kids.pop() )
        
        if not node.kids: return result 
        
    result = label_node(node)
    tag = result.tag
    
    while final_punctuation_stk:
        result = Node(tag, [result, final_punctuation_stk.pop()])
        
    return result
    
def inherit_tag(node, other):
    '''Gives _node_ the tag that _other_ has, unless _node_ already has one, or _other_ doesn't.'''
    if node.tag.find(":") == -1 and other.tag.find(":") != -1:
        node.tag += other.tag[other.tag.find(":"):]
    
#@echo
def label_node(node, inside_np_internal_structure=False):
    if node.is_leaf(): return node
    elif node.count() == 1:
        if ((inside_np_internal_structure and node.tag.startswith("NP") and has_noun_tag(node.kids[0])) or
            (node.tag.startswith("VP") and has_verbal_tag(node.kids[0])) or
            (node.tag.startswith("ADJP") and node.kids[0].tag.startswith("JJ")) or
            (node.tag.startswith("ADVP") and node.kids[0].tag in ("AD", "CS")) or
            (node.tag.startswith("CLP") and node.kids[0].tag==("M")) or
            (node.tag.startswith("QP") and node.kids[0].tag in ("OD","CD")) or
            (node.tag.startswith("DP") and node.kids[0].tag==("DT"))):
            replacement = node.kids[0]
            inherit_tag(replacement, node)
            replace_kid(node.parent, node, node.kids[0])
            return label_node(replacement)
            
        elif node.tag.startswith('NP') and node.kids[0].tag == "PN":
            replacement = node.kids[0]
            inherit_tag(replacement, node)
            replace_kid(node.parent, node, node.kids[0])
            replacement.tag = node.tag
            
            return label_node(replacement)
            
        else:
            node.kids[0] = label_node(node.kids[0])
            return node
    elif is_predication(node):
        return label_predication(node)
    elif is_np_structure(node):
        return label_adjunction(node, inside_np_internal_structure=True) # TODO: misnomer
    elif is_np_internal_structure(node):
        return label_np_internal_structure(node)
    elif (is_apposition(node)
       or is_modification(node)
       or is_adjunction(node)
       # TODO: what to do about VC?
       or is_verb_compound(node)):
        return label_adjunction(node)
    elif is_head_final(node):
        return label_head_final(node)
    elif is_head_initial(node):
        return label_head_initial(node)
    elif is_coordination(node):
        return label_coordination(node, inside_np_internal_structure=inside_np_internal_structure)
    else:
        return label_adjunction(node)
        
class Binariser(Filter, OutputDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputDerivation.__init__(self)
        self.outdir = outdir
        
    def accept_derivation(self, bundle):
        bundle.derivation = label_root(bundle.derivation)
        self.write_derivation(bundle)
    
if __name__ == '__main__':
    docs = parse_tree(sys.stdin.read())

    for root in docs:
        # if is_predication(root):
        #     result = Node(root.tag, [
        #         label_subject(root[0]),
        #         label_predicate(root[1])
        #     ])
        # else:
        result = label_root(root)
            
        print pprint(result)