# coding: utf-8
from __future__ import with_statement
import sys, re, os

from munge.trees.traverse import nodes
from munge.penn.io import parse_tree
from munge.penn.aug_nodes import Leaf, Node
from munge.trees.pprint import pprint
from munge.proc.filter import Filter
from munge.util.err_utils import debug
from munge.util.func_utils import twice

from apps.identify_lrhca import *
from apps.cn.output import OutputPrefacedPTBDerivation
from apps.cn.fix_utils import *
from apps.util.echo import *

def strip_tag_if(cond, tag):
    '''Strips the given _tag_ to its base if _cond_ is True.'''
    if cond:
        return base_tag(tag, strip_cptb_tag=False)
    else:
        return tag

#@echo
def label_adjunction(node, inherit_tag=False, do_labelling=True, inside_np_internal_structure=False):
    kid_tag = strip_tag_if(not inherit_tag, node.tag)
    
    if do_labelling:
        kids = map(lambda node: label_node(node, inside_np_internal_structure=inside_np_internal_structure), node.kids)
    else:
        kids = node.kids
    
#    last_kid, second_last_kid = twice(kids.pop)()
    last_kid, second_last_kid = twice(get_kid_)(kids)
    
    cur = Node(kid_tag, [second_last_kid, last_kid], head_index=1)
    
    while kids:
    #    kid = kids.pop()
        kid = get_kid_(kids)
        cur = Node(kid_tag, [kid, cur], head_index=1)
    
    cur.tag = node.tag
    return cur

def label_apposition(node, inherit_tag=False, inside_np_internal_structure=False):
    kid_tag = strip_tag_if(not inherit_tag, node.tag)
    
    if node.count() > 2:
        # Label the first kid before removing it from the node: if we did this the
        # other way around, then shrinking (which relies on replace_kid) would not
        # find _node[0]_ among the kids of _node_, and fail.
        first = label_node(node[0], inside_np_internal_structure=inside_np_internal_structure)
        node.kids.pop(0)
        
        return Node(kid_tag, [first, label_node(node)], head_index=0)
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
        
        return Node(old_tag, [ label_np_internal_structure(node), etc ], head_index=1)
    else:
        return label_adjunction(node, inside_np_internal_structure=True)

def label_with_final_punctuation_high(f):
    def _label(node, *args, **kwargs):
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
        
        result = f(node, *args, **kwargs)
        tag = result.tag
        
        while final_punctuation_stk:
            result = Node(tag, [result, final_punctuation_stk.pop()], head_index=0)
        
        return result
    return _label

#@echo
def _label_coordination(node, inside_np_internal_structure=False):
    if (node.kids[-1].tag.endswith(':&')
        # prevent movement when we have an NP with only two children NN ETC
        and node.count() > 2):
        
        etc = node.kids.pop()
        kid_tag = base_tag(node.tag, strip_cptb_tag=False)
        
        old_tag = node.tag
        node.tag = kid_tag
        
        return Node(old_tag, [ label_coordination(node, inside_np_internal_structure), etc ], head_index=1)
    else:
        def label_nonconjunctions(kid):
            if kid.tag not in ('CC', 'PU'):
                return label_node(kid, inside_np_internal_structure=inside_np_internal_structure)
            else: return kid
        
        kids = map(label_nonconjunctions, node.kids)
        return reshape_for_coordination(Node(node.tag, kids, head_index=0), inside_np_internal_structure=inside_np_internal_structure)

label_coordination = label_with_final_punctuation_high(_label_coordination)

def get_kid(kids, seen_cc):
    pu = kids.pop()
    
    if seen_cc and pu.tag == 'PU' and len(kids) > 0:
        xp = kids.pop()
        xp_ = Node(xp.tag, [xp, pu], head_index=0)
        
        return xp_, False
    else:
        return pu, pu.tag == 'CC'

def get_kid_(kids):
    return get_kid(kids, True)[0]

def reshape_for_coordination(node, inside_np_internal_structure):
    if node.count() >= 3:
        # (XP PU) (CC XP)
        # if we get contiguous PU CC, associate the PU with the previous conjunct
        # but:
        # XP (PU XP) (CC XP)
        # XP (PU XP PU) (CC XP)
        # the rule is:
        # attach PU to the right _unless_ it is followed by CC
        
        kid_tag = base_tag(node.tag, strip_cptb_tag=False)
        
        kids = node.kids
        
        seen_cc = False
        last_kid, seen_cc = get_kid(kids, seen_cc)
        second_last_kid, seen_cc = get_kid(kids, seen_cc)
        
        cur = Node(kid_tag, [second_last_kid, last_kid], head_index=1)
        
        while kids:
            kid, seen_cc = get_kid(kids, seen_cc)
            cur = Node(kid_tag, [kid, cur], head_index=1)
        
        cur.tag = node.tag
        return cur
    
    return label_adjunction(node, inside_np_internal_structure=inside_np_internal_structure, do_labelling=False)

#@echo
def label_head_initial(node, inherit_tag=False):
    kid_tag = strip_tag_if(not inherit_tag, node.tag)
    
    kids = map(label_node, node.kids)[::-1]
    first_kid, second_kid = twice(kids.pop)()
    
    cur = Node(kid_tag, [first_kid, second_kid], head_index=0)
    
    while kids:
        kid = kids.pop()
        cur = Node(kid_tag, [cur, kid], head_index=0)
    
    cur.tag = node.tag
    return cur

#@echo
def label_head_final(node):
    return label_adjunction(node)

def is_right_punct_absorption(node):
    return node.count() == 2 and node.tag == node[0].tag and node[1].tag == 'PU'

#@echo
def label_predication(node, inherit_tag=False):
    kid_tag = strip_tag_if(not inherit_tag, node.tag)
    
    kids = map(label_node, node.kids)
    last_kid, second_last_kid = twice(get_kid_)(kids)
    
    cur = Node(kid_tag, [second_last_kid, last_kid], head_index=1)
    
    while kids:
        kid = get_kid_(kids)
        cur = Node(kid_tag, [kid, cur], head_index=1)
    
    cur.tag = node.tag # restore the full tag at the topmost level
    
    return cur

#@echo
def label_root(node):
    final_punctuation_stk = []
    
    # These derivations consist of a leaf PU root: 24:73(4), 25:81(4), 28:52(21)
    if node.is_leaf():
        return node
    # inconsistent top-level taggings (0:21(4)) lead to a CCG-like absorption analysis
    elif is_right_punct_absorption(node):
        return label_node(node, do_shrink=False)
    
    elif all(kid.tag.startswith('PU') for kid in node):
        # Weird derivation (5:0(21)):
        # ((FRAG (PU --) (PU --) (PU --) (PU --) (PU --) (PU -)))
        return label_adjunction(node)
    
    while (not node.is_leaf()) and node.kids[-1].tag.startswith('PU'):
        final_punctuation_stk.append( node.kids.pop() )
        
        if not node.kids: return result # is this reachable?
    
    if node.count() == 1:
        node.head_index = 0
        result = label_node(node[0], do_shrink=False)
    else:
        result = label_node(node, do_shrink=False)
    
    tag = result.tag
    
    while final_punctuation_stk:
        result = Node(tag, [result, final_punctuation_stk.pop()], head_index=0)
    
    return result

PunctuationPairs = frozenset(
    # Our CCGbank tags for these paired punctuation tags are:
    # XQU XCS XPA XPA XSQ XTL XCD XCS (where X denotes one of L, R)
    ("“”", "「」", "（）", "()", "‘’", "《》", "『』", "「」")
)
def are_paired_punctuation(p1, p2):
    return p1 + p2 in PunctuationPairs

def has_paired_punctuation(node):
    # if node has fewer than 3 kids, the analysis is the same as the default (right-branching)
    return (node.count() > 3 and node.kids[0].is_leaf() and node.kids[-1].is_leaf() and
            are_paired_punctuation(node.kids[0].lex, node.kids[-1].lex))

def hoist_punctuation_then(label_func, node):
    # Do not hoist paired punctuation inside a parenthetical
    if node.tag.endswith(':p'): return label_func(node)
    
    initial = node.kids.pop(0)
    final = node.kids.pop()
    
    return Node(node.tag, [initial, Node(node.tag, [ label_func(node), final ], head_index=0)], head_index=1)

def label_node(node, *args, **kwargs):
    if node.count() == 1: node.head_index = 0
    if node.is_leaf() or node.count() == 1: return _label_node(node, *args, **kwargs)
    
    if has_paired_punctuation(node):
        return hoist_punctuation_then(_label_node, node)
    else:
        return _label_node(node, *args, **kwargs)

def matches(node, *matches):
    return any(node.tag.startswith(match) for match in matches)

def exactly_matches(node, *matches):
    return node.tag in matches

#@echo
def _label_node(node, inside_np_internal_structure=False, do_shrink=True):
    if node.is_leaf(): return node
    elif node.count() == 1:
        node.head_index = 0

        # shrinkage rules (NP < NN shrinks to NN)
        if (do_shrink and
            
            ((inside_np_internal_structure and
                ((node.tag.startswith('NP') 
                    and (not node.tag.endswith(':A')) 
                    and has_noun_tag(node[0])) or
                node[0].tag == 'AD')) or
            (node.tag.startswith('VP') or is_verb_compound(node)) and  # a handful of VRDs project a single child (11:29(4))
                (has_verbal_tag(node[0]) or 
                 matches(node[0], 'VPT', 'VSB', 'VRD', 'VCD', 'VNV', 'AD', 'PP', 'QP', 'LCP', 'NP')) or
            (node.tag.startswith('ADJP') and matches(node[0], 'JJ', 'AD', 'NN')) # bad tagging 25:40(5)
            ) or
            (node.tag.startswith('ADVP') and exactly_matches(node[0], 'AD', 'CS', 'NN')) or
            (matches(node, 'NP-MNR', 'NP-PRP') and has_noun_tag(node[0])) or
            # 8:1(5)
            (node.tag == 'NP-PN:a' and exactly_matches(node[0], 'NR')) or
            (node.tag.startswith('CLP') and exactly_matches(node[0], 'M')) or
            (node.tag.startswith('LCP') and exactly_matches(node[0], 'LC')) or
            # DT < OD found in 6:25(11)
            (node.tag.startswith('DP') and exactly_matches(node[0], 'DT', 'OD')) or
            # QP < AD in 24:68(8)
            (node.tag.startswith('QP') and matches(node[0], 'QP', 'M')) or
            # see head-initial case in tag.py (hack for unary PP < P)
            (node.tag.startswith('PP') and exactly_matches(node[0], 'P')) or
            # see bad tagging (WHNP CP DEC) in tag.py head-final case
            (node.tag.startswith('CP') and matches(node[0], 'IP')) or
            (node.tag.startswith('INTJ') and exactly_matches(node[0], 'IJ')) or
            (node.tag.startswith('LST') and exactly_matches(node[0], 'OD', 'CD')) or
            # the below is to fix a tagging error in 10:49(69)
            (node.tag.startswith('PRN') and exactly_matches(node[0], 'PU')) or
            # 0:15(5) LST < PU
            (node.tag.startswith('LST') and exactly_matches(node[0], 'PU')) or
            matches(node, 'FLR') or matches(node, 'FW')):
            
            replacement = node[0]
            inherit_tag(replacement, node, strip_marker=True)
            replace_kid(node.parent, node, node[0])
            return label_node(replacement)
            
        # NN for 25:61(7)
        elif (node.tag.startswith("QP") and exactly_matches(node[0], "OD", "CD", 'NN')):
            
            replacement = node[0]
            inherit_tag(replacement, node)
            replace_kid(node.parent, node, node[0])
            #replacement.tag = node.tag
            
            return label_node(replacement)
        
        # promotion rules (NP < PN shrinks to NP (with PN's lexical item and pos tag))
        # shrink NP-TMP < NT so that the NT lexical item gets the adjunct category
        elif ((node.tag.startswith('NP') and (exactly_matches(node[0], "PN") or matches(node[0], 'NT', 'DT'))) or
              # 21:2(6)
              (node.tag.startswith('ADVP') and exactly_matches(node[0], 'CC', 'PN')) or

              (node.tag.startswith('ADJP') and exactly_matches(node[0], 'PN', 'DT')) or
              # 28:82(8)
              (node.tag.startswith('DP') and matches(node[0], 'NN', 'PN')) or
              (matches(node, #'NP-PRD', 'NP-TTL-PRD', 'NP-PN-PRD', 
                             'NP-LOC', 'NP-ADV',
                             'NP-PN-TMP', 'NP-PN-LOC', 'NP-TMP', 'NP-DIR', 'NP-PN-DIR')
                  and has_noun_tag(node[0]))):
                  
            replacement = node[0]
            inherit_tag(replacement, node)
            replace_kid(node.parent, node, node[0])
            #replacement.tag = node.tag
            
            return label_node(replacement)
        
        # one child nodes
        else:
            node.kids[0] = label_node(node.kids[0])
            return node
    
    elif is_S_NP_apposition(node):
        inherit_tag(node[1][0], node[1])
        node.kids[1] = node[1][0]
        return label_head_final(node)
    
    elif is_predication(node):
        return label_predication(node)
    elif is_prn(node):
        # although we want a head-initial analysis, we want a right-branching structure
        return label_adjunction(node, inside_np_internal_structure=True)
    elif is_apposition(node):
        return label_apposition(node, inside_np_internal_structure=True)
    elif is_np_structure(node):# and not node[0].tag.startswith('IP-APP'):
        return label_adjunction(node, inside_np_internal_structure=True) # TODO: misnomer
    elif is_np_internal_structure(node):
        return label_np_internal_structure(node)
    # 0:68(4) has both cases. If there are NP modifiers of a QP or an ADJP, we want them shrunk.
    elif node.kids[-1].tag in ('QP:h', 'ADJP:h'):
        return label_adjunction(node, inside_np_internal_structure=True)
    elif (is_adjunction(node)
       or is_verb_compound(node)
       or is_modification(node)):
        return label_adjunction(node)
    elif is_head_final(node):
        return label_head_final(node)
    elif is_head_initial(node):
        return label_head_initial(node)
    elif is_coordination(node) or is_ucp(node):
        return label_coordination(node, inside_np_internal_structure=inside_np_internal_structure)
    else:
        return label_adjunction(node)

class Binariser(Filter, OutputPrefacedPTBDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPrefacedPTBDerivation.__init__(self, outdir)
    
    def accept_derivation(self, bundle):
        bundle.derivation = label_root(bundle.derivation)
        self.write_derivation(bundle)
    
    opt = '2'
    long_opt = 'binarise'
    
    arg_names = 'OUTDIR'
    
