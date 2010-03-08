from __future__ import with_statement
import sys, re, os

from munge.trees.traverse import nodes
from munge.penn.io import parse_tree
from munge.penn.nodes import Leaf, Node
from munge.trees.pprint import pprint
from munge.proc.filter import Filter
from munge.util.err_utils import debug

from apps.identify_lrhca import *
from apps.cn.output import OutputDerivation
from apps.cn.fix_utils import *
from apps.util.echo import *

def strip_tag_if(cond, tag):
    if cond:
        return base_tag(tag, strip_cptb_tag=False)
    else:
        return tag

#@echo
def label_adjunction(node, inherit_tag=False, without_labelling=False, inside_np_internal_structure=False):
    kid_tag = strip_tag_if(not inherit_tag, node.tag)

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
    
def label_apposition(node, inherit_tag=False):
    kid_tag = strip_tag_if(not inherit_tag, node.tag)

    if node.count() > 2:
        first, rest = node.kids.pop(0), node.kids
        return Node(kid_tag, [label_node(first), label_node(node)])
    return label_adjunction(node, inherit_tag=inherit_tag)
    
#@echo
def label_np_internal_structure(node, inherit_tag=False):
    if (node.kids[-1].tag.endswith(':&') 
        # prevent movement when we have an NP with only two children NN ETC
        and node.count() > 2):
        
        etc = node.kids.pop()
        kid_tag = strip_tag_if(not inherit_tag, node.tag)
        
        old_tag = node.tag
        node.tag = kid_tag
        
        return Node(old_tag, [ label_np_internal_structure(node), etc ])
    else:
        return label_adjunction(node, inside_np_internal_structure=True)
    
#@echo
def label_coordination(node, inside_np_internal_structure=False):
    if (node.kids[-1].tag.endswith(':&') 
        # prevent movement when we have an NP with only two children NN ETC
        and node.count() > 2):

        etc = node.kids.pop()
        kid_tag = strip_tag_if(not inherit_tag, node.tag)

        old_tag = node.tag
        node.tag = kid_tag

        return Node(old_tag, [ label_coordination(node, inside_np_internal_structure), etc ])
    else:
        def label_nonconjunctions(kid):
            if kid.tag not in ('CC', 'PU'): 
                return label_node(kid, inside_np_internal_structure=inside_np_internal_structure)
            else: return kid

        kids = map(label_nonconjunctions, node.kids)
        return reshape_for_coordination(Node(node.tag, kids), inside_np_internal_structure=inside_np_internal_structure)
        
def get_kid(kids, node_tag, seen_cc):
    pu = kids.pop()

    if seen_cc and pu.tag == 'PU' and len(kids) > 0:
        xp = kids.pop()
        xp_ = Node(xp.tag, [xp, pu])
        
        return xp_, False
    else:
        return pu, pu.tag == 'CC'
        
def reshape_for_coordination(node, inside_np_internal_structure):
    if node.count() >= 3:
        # (XP PU) (CC XP)
        # if we get contiguous PU CC, associate the PU with the previous conjunct
        # but:
        # XP (PU XP) (CC XP)
        # XP (PU XP PU) (CC XP)
        # the rule is:
        # attach PU to the right _unless_ it is followed by CC
        # easier to iterate in reverse?
        
        kid_tag = strip_tag_if(not inherit_tag, node.tag)

        kids = node.kids
        
        seen_cc = False
        last_kid, seen_cc = get_kid(kids, kid_tag, seen_cc)
        second_last_kid, seen_cc = get_kid(kids, kid_tag, seen_cc)

        cur = Node(kid_tag, [second_last_kid, last_kid])

        while kids:
            kid, seen_cc = get_kid(kids, kid_tag, seen_cc)
            cur = Node(kid_tag, [kid, cur])

        cur.tag = node.tag
        return cur
            
    return label_adjunction(node, inside_np_internal_structure=inside_np_internal_structure, without_labelling=True)
        
#@echo
def label_head_initial(node, inherit_tag=False):
    kid_tag = strip_tag_if(not inherit_tag, node.tag)
    
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
    
    kid_tag = strip_tag_if(not inherit_tag, node.tag)

    # TODO: think of a better and more general way of doing this
    # this is to stop what happens in 2:4(2) with PU. what is actually happening?
    # if is_left_punct_absorption(second_last_kid):
    #     initial_tag = 'VP'
    # else:
    #     initial_tag = kid_tag
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
    
    # These derivations consist of a leaf PU root: 24:73(4), 25:81(4), 28:52(21)
    if node.is_leaf():
        return node
    elif all(kid.tag.startswith('PU') for kid in node):
        # Weird derivation (5:0(21)):
        # ((FRAG (PU --) (PU --) (PU --) (PU --) (PU --) (PU -)))
        return label_adjunction(node)
    
    while (not node.is_leaf()) and node.kids[-1].tag.startswith('PU'):
        final_punctuation_stk.append( node.kids.pop() )
        
        if not node.kids: return result 
        
    result = label_node(node, do_shrink=False)
    tag = result.tag
    
    while final_punctuation_stk:
        result = Node(tag, [result, final_punctuation_stk.pop()])
        
    return result
    
#@echo
def label_node(node, inside_np_internal_structure=False, do_shrink=True):
    if node.is_leaf(): return node
    elif node.count() == 1:
        # shrinkage rules (NP < NN shrinks to NN)
        if (do_shrink and ((inside_np_internal_structure and node.tag.startswith("NP") and 
                has_noun_tag(node.kids[0])
                or node.kids[0].tag == "AD") or
            # (node.tag.startswith("NP-PRD") and
            #     node.kids[0].tag.startswith("CP")) or
            ( (node.tag.startswith("VP") or
                    is_verb_compound(node))  # a handful of VRDs project a single child (11:29(4))
                and (has_verbal_tag(node.kids[0]) 
                 or any(node.kids[0].tag.startswith(cand) for cand in ('VPT', 'VSB', 'VRD', 'VCD', 'VNV'))
                 or node.kids[0].tag.startswith("AD")
                 or any(node.kids[0].tag.startswith(cand) for cand in ('PP-PRD', 'QP-PRD', 'LCP-PRD'))
            ) ) or
            # shrink NP-TMP < NT so that the NT lexical item gets the adjunct category
            (node.tag.startswith('NP') and node.kids[0].tag.startswith('NT')) or
            (any(node.tag.startswith(cand) for cand in ('NP-LOC', 'NP-ADV', 'NP-PN-LOC', 'NP-TMP', 'NP-DIR', 'NP-PN-DIR'))
                and has_noun_tag(node.kids[0])) or
            (node.tag.startswith("ADJP") and 
                (node.kids[0].tag.startswith("JJ") 
                 or node.kids[0].tag.startswith("AD"))) or
            (node.tag.startswith("ADVP") and node.kids[0].tag in ("AD", "CS")) or
            (node.tag.startswith("CLP") and node.kids[0].tag == "M") or  
            (node.tag.startswith("LCP") and node.kids[0].tag == "LC") or  
            # DT < OD found in 6:25(11)
            (node.tag.startswith("DP") and node.kids[0].tag in ("DT", "OD")) or
            # QP < AD in 24:68(8)
            (node.tag.startswith("QP") and node.kids[0].tag.startswith("QP")) or
            # see head-initial case in tag.py (hack for unary PP < P)
            (node.tag.startswith('PP') and node.kids[0].tag == "P") or
            # see bad tagging (WHNP CP DEC) in tag.py head-final case
            (node.tag.startswith('CP') and node.kids[0].tag.startswith('IP')) or
            (node.tag.startswith('INTJ') and node.kids[0].tag == 'IJ') or
            (node.tag.startswith("LST") and node.kids[0].tag == "OD") or
            # the below is to fix a tagging error in 10:49(69)
            (node.tag.startswith('PRN') and node.count() == 1 and node.kids[0].tag == 'PU') or
            (node.tag.startswith('FLR')) or (node.tag.startswith('FW')))):

            replacement = node.kids[0]
            inherit_tag(replacement, node)
            replace_kid(node.parent, node, node.kids[0])
            return label_node(replacement)
            
        # promotion rules (NP < PN shrinks to NP (with PN's lexical item and pos tag))
        elif ((node.tag.startswith('NP') and node.kids[0].tag == "PN") or
              (node.tag.startswith("QP") and node.kids[0].tag in ("OD", "CD"))):
            replacement = node.kids[0]
            inherit_tag(replacement, node)
            replace_kid(node.parent, node, node.kids[0])
            replacement.tag = node.tag
            
            return label_node(replacement)
            
        # one child nodes
        else:
            node.kids[0] = label_node(node.kids[0])
            return node
            
    elif is_predication(node):
        return label_predication(node)
    elif is_prn(node):
        return label_head_final(node)
    elif is_apposition(node):
        return label_apposition(node)
    elif is_np_structure(node):
        return label_adjunction(node, inside_np_internal_structure=True) # TODO: misnomer
    elif is_np_internal_structure(node):
        return label_np_internal_structure(node)
    elif (is_apposition(node)
       or is_modification(node)
       or is_adjunction(node)
       or is_verb_compound(node)):
        return label_adjunction(node)
    elif is_head_final(node):
        return label_head_final(node)
    elif is_head_initial(node):
        return label_head_initial(node)
    elif is_coordination(node) or is_ucp(node):
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
        
    opt = '2'
    long_opt = 'binarise'
    
    arg_names = 'OUTDIR'
    