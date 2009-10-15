# coding=utf-8
from __future__ import with_statement
from copy import copy
from munge.proc.filter import Filter
from apps.cn.output import OutputDerivation

from apps.cn.fix_utils import shrink_left
from munge.util.err_utils import warn, info

import sys, os

import apps.util.echo as E
from munge.trees.pprint import *
from apps.identify_lrhca import *
from munge.cats.nodes import *
from munge.cats.cat_defs import *
import munge.penn.aug_nodes as A

from apps.cn.fix_utils import *

def tag_and_lex(node):
    return node.tag + "/" + node.lex
    
def tag_and_text_under(node):
    return "%s/(%s)" % (node.tag, ' '.join(node.text()))
    
def print_lrp(node):
    if isinstance(node, A.Node):
        return "%s (%s)" % (node.tag, " ".join(tag_and_text_under(x) for x in node))
    elif isinstance(node, A.Leaf):
        return "%s" % tag_and_lex(node)
    else:
        return repr(node)
def echo(fn, write=sys.stdout.write):
    return E.echo(fn, print_lrp, write)

def rename_category_while_labelling_with(label_function, node, substitute, when=None):
    if when and (not when(node.category)): return label_function(node)
    
    old_category = node.category
    node.category = substitute
    
    ret = label_function(node)
    
    node.category = old_category
    
    return ret
    
#@echo
def label_predication(node):
    node.kids[0] = label(node[0])
    
    node[1].category = node.category | node[0].category
    node.kids[1] = label(node[1])
    
    return node
    
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

    # if the modifier category (lhs) has a special functor (like NP/N), use that
    node[0].category = (
#            np_modifier_tag_to_cat(node[0].tag) or 
            (featureless(node.category) / featureless(node[1].category)))
            
    node.kids[0] = label(node[0])
    
    return node
    
def label_np_structure(node):
    node[0].category = node.category / node.category
    node.kids[0] = label(node[0])
    if node.count() > 1:
        node[1].category = node.category
        node.kids[1] = label(node[1])
        
    return node
    
@echo
def label_right_adjunction(node):
    node[0].category = node.category
    node.kids[0] = label(node[0])
    
    no_features = featureless(node.category)
    node[1].category = no_features | no_features
    print "node[1] got %s" % node[1].category
    node.kids[1] = label(node[1])

    return node
    
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
    
#@echo
def label_coordination(node, inside_np=False):
    node[0].category = node.category
    node.kids[0] = label(node[0], inside_np)

    node[1].category = node.category
    node.kids[1] = label(node[1])    
    node[1].category = node.category.clone().add_feature('conj')

    return node
    
#@echo
def label_partial_coordination(node, inside_np=False):
    node[0].category = ptb_to_cat(node[0])
    node.kids[0] = label(node[0], inside_np)

#    node[1].category = node.category.clone().add_feature('conj')
    node[1].category = node.category
    node.kids[1] = label(node[1], inside_np)
    
    return node
    
# If no process successfully assigns a category, these are used to map PTB tags to
# a 'last-ditch' category.
Map = {
    'NP': NP,
    'PN': NP,
    
    'NN': N,
    'NR': N,
    'NT': N,
    
    'IP': Sdcl,
    'CP-Q': Sq,

    'ADVP': SbNPfSbNP,
    
    'VP': SdclbNP,
    'VA': SdclbNP,
    'VV': SdclbNP,
    
    'CC': conj
    
    #'CP': C('NP/NP'),
}

PunctuationMap = {
    '.': '.', # Roman period
    '。': '.', # Chinese period
    
    '、': 'LCM', # Enumeration comma (顿号) for separating list items
    '，': ',', # Clausal comma (逗号)
    ',': ',', # Roman comma
    
    '？': '?', # Chinese question mark
    '?': '?',
    
    '！': '!', # Chinese exclamation mark
    '!': '!',
    
    '：': ':', # Chinese colon
    ':': ':',
    
    '；': ';', # Chinese semicolon
    ';': ':',
    
    '（': 'LPA', # Chinese opening paren
    '(': 'LPA',
    
    '）': 'RPA', # Chinese closing paren
    ')': 'RPA',
}
##@echo
def ptb_to_cat(node, return_none_when_unmatched=False):
    if node.tag == 'PU' and node.lex in PunctuationMap:
        return AtomicCategory(PunctuationMap[node.lex])
        
    original_tag = node.tag
    stemmed_tag = base_tag(node.tag)
    
    ret = Map.get(original_tag, None)
    return copy(Map.get(original_tag, None)
             or Map.get(stemmed_tag, None if return_none_when_unmatched else AtomicCategory(stemmed_tag )))
    
NPModifierMap = {
#    'QP': C('NP/NP'),
#    'QP-OBJ': C('NP/NP'),

    # 'ADJP': C('N/N'),
    # 'CP': C('N/N'),
    # 'QP': C('NP/N'),
    # 'DP': C('NP/N'),
    
    # 'ADJP': C('NP/NP'),
    'CP': C('NP/NP'),
    # 'QP': C('NP/NP'),
    # 'DP': C('NP/NP'),
#    'ADVP': C('NP/NP')
}    
def np_modifier_tag_to_cat(ptb_tag):
    ptb_tag = base_tag(ptb_tag)
    return copy(NPModifierMap.get(ptb_tag, None))
    
#@echo
def label_verb_compound(node):
    node[0].category = conj if node[0].tag == 'CC' else node.category
    node[1].category = conj if node[1].tag == 'CC' else node.category
    
    if node[0].tag == 'CC':
        node[0].category = conj
        node[1].category = node.category
    elif node[1].tag == 'CC':
        node[1].category = conj
        node[0].category = node.category
    else:
        node[0].category = node.category
        node[1].category = node.category | node.category # TODO:
    
    node.kids[0] = label(node[0])
    node.kids[1] = label(node[1])
    
    return node
    
def is_cp_to_np_nominalisation(node):
    return (node.count() == 1 and
            node.tag.startswith('NP') and
            node[0].tag.startswith('CP'))
            
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
        print "is_cp_to_np_nominalisation(%s)" % node
        node[0].category = C('NP/NP')
        node.kids[0] = label(node[0])
        
        return node
        
    elif (node.count() == 1
       or is_topicalisation(node) 
       or is_topicalisation_without_gap(node)
       or is_apposition(node)
       or is_modification(node)):
       
        node.kids[0] = label(node[0])
        if node.count() > 1:
            node.kids[1] = label(node[1])
            
        return node
        
    elif is_etc(node):
        return label_head_final(node)
        
    elif is_verb_compound(node):
        if not node.category:
            node.category = node.parent.category # VP < VRD, ...
        return label_verb_compound(node)
        
    elif is_left_absorption(node):
        return label_left_absorption(node)
    elif is_right_absorption(node):
        return label_right_absorption(node)
        
    # must be above predication
    elif is_PRO_trace(node):
        new_node = shrink_left(node, node.parent)
        ret = label(new_node)
        return ret

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

def label_root(node):
    node.category = ptb_to_cat(node)
    node = label(node)
    return node

class LabelNodes(Filter, OutputDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputDerivation.__init__(self)
        
        self.outdir = outdir
        
    def accept_derivation(self, bundle):
        bundle.derivation = label_root(bundle.derivation)
        
        self.write_derivation(bundle)