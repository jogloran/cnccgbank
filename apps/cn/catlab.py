# coding=utf-8
from __future__ import with_statement
import sys, os
from copy import copy

from munge.proc.filter import Filter
from munge.util.err_utils import warn, info
from munge.util.deco_utils import memoised

from munge.trees.pprint import *
from munge.cats.nodes import *
from munge.cats.cat_defs import *
from munge.trees.traverse import lrp_repr, nodes

import apps.util.echo as E

from apps.cn.fix_utils import *
from apps.identify_lrhca import *
from apps.cn.output import OutputDerivation

def echo(fn, write=sys.stdout.write):
    return E.echo(fn, lrp_repr, write)

def rename_category_while_labelling_with(label_function, node, substitute, when=None):
    '''Applies the labelling function _label_function_ to the given _node_, replacing
its category with _substitute_ before labelling, and re-instating the former category
afterwards, when the predicate _when_ is true for the node's category.'''
    if when and (not when(node.category)): return label_function(node)
    
    old_category = node.category
    node.category = substitute
    
    ret = label_function(node)
    
    node.category = old_category
    
    return ret
    
#@echo
def label_head_final(node):
    node.kids[0] = label(node[0])

    node[1].category = node.category | node[0].category
    node.kids[1] = label(node[1])

    return node

#@echo
def label_head_initial(node):
    node.kids[1] = label(node[1])

    node[0].category = node.category / node[1].category
    node.kids[0] = label(node[0])

    return node

label_predication = label_head_final

#@echo
def label_left_absorption(node):
    node[0].category = ptb_to_cat(node[0])
    
    node[1].category = node.category
    node.kids[1] = label(node[1])
    
    return node

#@echo
def label_right_absorption(node):
    node[1].category = ptb_to_cat(node[1])
    
    node[0].category = node.category
    node.kids[0] = label(node[0])
    
    return node

#@echo
def label_adjunction(node):
    node[1].category = ptb_to_cat(node[1], return_none_when_unmatched=True) or node.category
    node.kids[1] = label(node[1])
    
    node[0].category = featureless(node.category) / featureless(node[1].category)
    node.kids[0] = label(node[0])
    
    return node

#@echo
def label_np_structure(node):
    node[0].category = node.category / node.category
    node.kids[0] = label(node[0])
    if node.count() > 1:
        node[1].category = node.category
        node.kids[1] = label(node[1])
    
    return node

#@echo
def label_right_adjunction(node):
    node[0].category = node.category
    node.kids[0] = label(node[0])
    
    no_features = featureless(node.category)
    node[1].category = no_features | no_features
    node.kids[1] = label(node[1])
    
    return node

#@echo
def label_coordination(node, inside_np=False, ucp=False):
    node[0].category = node.category
    node.kids[0] = label(node[0], inside_np)
    
    node[1].category = ptb_to_cat(node[1]) if ucp else node.category
    # Label then apply [conj], so that kid categories don't inherit the feature
    node.kids[1] = label(node[1])
    node[1].category = node.category.clone_adding_feature('conj')
    
    return node

#@echo
def label_partial_coordination(node, inside_np=False, ucp=False):
    node[0].category = ptb_to_cat(node[0])
    node.kids[0] = label(node[0], inside_np)
    
    node[1].category = ptb_to_cat(node[1]) if ucp else node.category 
    node.kids[1] = label(node[1], inside_np)
    
    return node

# If no process successfully assigns a category, these are used to map PTB tags to
# a 'last-ditch' category.
Map = {
    'NP': NP, 'PN': NP,
    'DT': NP,
    
    'NN': N, 'NR': N, 'NT': N,
    
    'FRAG': Sfrg,
    'IP': Sdcl,
    'CP-Q': Sq,
    
    'ADVP': SbNPfSbNP,
    'AD': SbNPfSbNP,
    
    'VP': SdclbNP, 'VA': SdclbNP, 'VV': SdclbNP,
    # not really intended for use. FLR < VE (see the "Addendum to the Bracketing Guidelines for the ACE Chinese Broadcast News Data")
    # appears in 25:97(2). We'll just treat this as a noisy unary rule.
    'VE': SdclbNP,
#    'VC': SdclbNPfNP,
    
    'VSB': SdclbNP, 'VRD': SdclbNP, 'VCD': SdclbNP, 'VNV': SdclbNP, 'VPT': SdclbNP,
    'CC': conj,
    
    'CD': Nnum,
    # to account for noise in 25:43(4)
    'OD': NfN, 
    
    'ADJP': NfN,
    'JJ': NfN,
    # to account for CLP modification (the modifiers should end up as M/M, see 0:9(3))
    'CLP': C('M'),
    'DP': C('NP/N'),
    
    'FW': N, # last ditch for filler words
    
    'CP-PRD': NP,
    'CP-OBJ': Sdcl, # 8:16(9) CP in object position is treated as IP
    'CP-CND': SfS,
    'CP-ADV': SfS,
}

PunctuationMap = {
    '.': '.', # Roman period
    '。': '.', # Chinese period
    
    '、': 'LCM', # Enumeration comma (顿号) for separating list items
    '，': ',', # Clausal comma (逗号)
    ',': ',', # Roman comma
    
    '？': '?', '?': '?', # Chinese question mark
    '！': '!', '!': '!', # Chinese exclamation mark
    
    '：': ':', ':': ':', # Chinese colon
    '；': ';', ';': ';', # Chinese semicolon
    
    '（': 'LPA', '(': 'LPA', # Chinese opening paren
    '）': 'RPA', ')': 'RPA', # Chinese closing paren
    
    '“': 'LQU', '”': 'RQU', # Roman double quote
    '‘': 'LSQ', '’': 'RSQ', # Roman single quote
    
    '—': 'DSH', # Chinese dash
    
    '《': 'LTL', '》': 'RTL', # Chinese title bracket
    '『': 'LCD', '』': 'RCD', # Chinese double corner bracket
    '「': 'LCS', '」': 'RCS', # Chinese left corner bracket
    
    '/': 'SLS', '//': 'SLS',
}

Dashes = set("── - --- ---- ━ ━━ — —— ———".split())
def is_dashlike(t):
    return t in Dashes
    
@memoised
def make_atomic_category(atom):
    return AtomicCategory(atom)
    
RootMap = {
    'CP': Sdcl,
    'IP': Sdcl,
    'CP-Q': Sq,
}

#@echo
def ptb_to_cat(node, return_none_when_unmatched=False, is_root=False):
    '''Given _node_, returns a category object based only on its treebank
tag, using the mapping. If _return_none_when_unmatched_ is True, None is
returned if the mapping yields no category; otherwise, an atomic category
is returned with the base CPTB tag. If _is_root_, a special mapping is
consulted first.'''
    if node.tag == 'PU' and node.is_leaf():
        if node.lex in PunctuationMap:
            return make_atomic_category(PunctuationMap[node.lex])
        elif is_dashlike(node.lex):
            return make_atomic_category('DSH')
        else:
            return make_atomic_category(',')
            
    # CP ending in SP (5:95(30)) should be treated as IP
    if node.tag.startswith("CP") and node[-1].tag.startswith("SP"):
        return Sdcl
    
    original_tag = base_tag(node.tag, strip_cptb_tag=False)
    stemmed_tag = base_tag(node.tag)
    
    ret = Map.get(original_tag, None)
    return copy((is_root and (RootMap.get(original_tag, None) or RootMap.get(stemmed_tag, None)))
             or Map.get(original_tag, None)
             or Map.get(stemmed_tag, None if return_none_when_unmatched else AtomicCategory(stemmed_tag)))

NPModifierMap = {
    'CP': C('NP/NP'),
}
def np_modifier_tag_to_cat(ptb_tag):
    ptb_tag = base_tag(ptb_tag)
    return copy(NPModifierMap.get(ptb_tag, None))

def is_cp_to_np_nominalisation(node):
    return (node.count() == 1 and
            node.tag.startswith('NP') and
            (node[0].tag.startswith('CP') or node[0].tag.startswith("DNP")))

def is_PRO_trace(node):
    return (node.count() >= 2 and node[0].count() == 1
            and node[0][0].tag == "-NONE-"
            and node[0][0].lex == "*PRO*")

#@echo
def label(node, inside_np=False):
    '''
    Labels the descendants of _node_ and returns _node_.
    '''
    if node.category is None:
        node.category = ptb_to_cat(node)
        
        # if this matches the IP root with a *PRO* trace under it, then
        # we shouldn't map IP -> S, but rather IP -> S\NP
        if has_noun_tag(node):
            node.category = N
        else:
            node.category = ptb_to_cat(node)
    
    if node.is_leaf():
        if not node.category:
            node.category = ptb_to_cat(node)
        return node
    
    # NP/NP (CP) -> NP
    elif is_cp_to_np_nominalisation(node):
        node[0].category = NPfNP
        node.kids[0] = label(node[0])
        
        return node
    
    # VSB is analysed as head-final
    elif node.tag.startswith('VSB'):
        node[1].category = node.category
        node.kids[1] = label(node[1])
        
        node[0].category = node.category / node[1].category
        node.kids[0] = label(node.kids[0])
        
        return node
        
    # VCD is treated like apposition
    elif node.tag.startswith('VCD'):
        if has_verbal_tag(node[0]):
            node[0].category = node.category
        else:
            node[0].category = ptb_to_cat(node[0])
            
        node.kids[0] = label(node[0])
            
        if has_verbal_tag(node[1]):
            node[1].category = node.category
        else:
            node[1].category = ptb_to_cat(node[1])
            
        node.kids[1] = label(node[1])
            
        return node
        
    elif node.tag.startswith('VRD'):
        return label_right_adjunction(node)
        
    elif node.tag.startswith('VNV'):
        if has_verbal_tag(node[0]):
            node[0].category = node.category
        elif node[0].tag.startswith('AD'):
            node[0].category = node.category / node.category
        else:
            node[0].category = ptb_to_cat(node)
            
        node.kids[0] = label(node[0])
        
        node[1].category = node.category
        node.kids[1] = label(node[1])
        
        return node

    # must be above is_apposition, because there exist NP-APP:a ETC:& cases
    elif is_etc(node):
        return label_head_final(node)
        
    elif (node.count() == 1
       or is_topicalisation(node)
       or is_topicalisation_without_gap(node)
       or is_apposition(node)
       or is_argument_cluster(node)
       or is_modification(node)):
        
        node.kids[0] = label(node[0])
        if node.count() > 1:
            node.kids[1] = label(node[1])
        
        return node
    
    elif is_partial_ucp(node):
        return label_partial_coordination(node, ucp=True)
    elif is_ucp(node):
        return label_coordination(node, ucp=True)
    
    elif is_left_absorption(node):
        return label_left_absorption(node)
    elif is_right_absorption(node):
        return label_right_absorption(node)
    
    elif is_predication(node):
        return label_predication(node)
    elif is_right_adjunction(node): # (:h :a), for aspect particles
        return label_right_adjunction(node)
            
    elif is_partial_coordination(node):
        return label_partial_coordination(node)
    elif is_coordination(node):
        return label_coordination(node)
    
    elif is_np_structure(node):
        return rename_category_while_labelling_with(
            label_np_structure,
            node, N,
            when=lambda category: category == NP)
    
    elif is_np_internal_structure(node):
        if node.category == NP:
            P = N
        else:
            P = node.category
        
        for kid in node:
            if kid.tag.endswith(':N'):
                kid.category = P
            elif kid.tag.endswith(':n'):
                kid.category = P/P
            elif kid.tag == 'CC':
                kid.category = conj
            elif kid.tag.startswith('NP'):
                kid.category = P
            else:
                kid.category = np_modifier_tag_to_cat(kid.tag)
        
        if node.count() == 1:
            node.category = node[0].category
        
        node.kids[0] = label(node[0])
        if node.count() > 1:
            node.kids[1] = label(node[1])
        
        return node
    
    elif is_adjunction(node):
        return label_adjunction(node)
    
    elif is_head_final(node):
        return label_head_final(node)
    elif is_head_initial(node):
        return label_head_initial(node)
    
    else:
        warn("Node did not match any known patterns -- assuming adjunction: %s",
            node.__repr__(suppress_lex=True))
        return label_adjunction(node)

def label_root(root):
    root.category = ptb_to_cat(root, is_root=True)
    
    for node in nodes(root):
        # remove PRO traces as a preprocessing step
        if is_PRO_trace(node):
            new_node = shrink_left(node, node.parent)
            new_node.tag = base_tag(new_node.tag, strip_cptb_tag=False)
            
            if not node.parent:
                root = new_node

            inherit_tag(new_node, node)
        
    return label(root)

class LabelNodes(Filter, OutputDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputDerivation.__init__(self)
        
        self.outdir = outdir
    
    def accept_derivation(self, bundle):
        bundle.derivation = label_root(bundle.derivation)
        
        self.write_derivation(bundle)
    
    opt = '3'
    long_opt = 'label'
    
    arg_names = 'OUTDIR'
