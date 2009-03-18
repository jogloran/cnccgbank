from __future__ import with_statement
from copy import copy
from munge.proc.filter import Filter
from apps.cn.output import OutputDerivation
from munge.util.err_utils import warn, info
import os

#from echo import *
from munge.trees.pprint import *
from apps.identify_lrhca import *
from munge.cats.nodes import *
from munge.cats.cat_defs import *
import munge.penn.aug_nodes as A

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
    node[0].category = node[0].tag
    
    node[1].category = node.category
    node.kids[1] = label(node[1])
    
    return node
    
#@echo
def label_right_absorption(node):
    node[1].category = node[1].tag
    
    node[0].category = node.category
    node.kids[0] = label(node[0])
    
    return node
    
#@echo
def label_adjunction(node):
    node[1].category = node.category
    node.kids[1] = label(node[1])    

    node[0].category = node.category / node.category
    node.kids[0] = label(node[0])
    
    return node
    
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
    
    node[1].category = node.category | node.category
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
def label_coordination(node):
    node[0].category = node.category
    node.kids[0] = label(node[0])

    node[1].category = node.category
    node.kids[1] = label(node[1])    
    node[1].category = node.category.clone().add_feature('conj')

    return node
    
#@echo
def label_partial_coordination(node):
    node[0].category = ptb_to_cat(node[0].tag)
    node.kids[0] = label(node[0])

#    node[1].category = node.category.clone().add_feature('conj')
    node[1].category = node.category
    node.kids[1] = label(node[1])
    
    return node
    
Map = {
    # 'NP-SBJ': NP,
    # 'NP-OBJ': NP,
    # 'NP-PN-SBJ': NP,
    # 'NP-PRD': NP,
    # 'NP-EXT': NP,
    # 'NP-TPC': NP,
     'NP': NP,
#    'NP': N,
    
    'NN': N,
    'NR': N,
    'NT': N,
    
    'IP-HLN': S,
    'IP': S,
    'IP-SBJ': S,
    'IP-OBJ': S,
#    'QP': C('NP/NP'),
#    'QP-OBJ': C('NP/NP'),
    'ADJP': C('N/N'),
    'QP': AtomicCategory('QP'),
    'CP': C('NP/NP'),
    'DP': C('N/N'),
    'LCP': AtomicCategory('LCP'),
    'LCP-OBJ': AtomicCategory('LCP'),
    'ADVP': SbNPfSbNP,
    'VP': SbNP,
    'PP-LOC': PP
}
#@echo
def ptb_to_cat(ptb_tag):
    ptb_tag = base_tag(ptb_tag)
    ptb_tag = Map.get(ptb_tag, AtomicCategory(ptb_tag))
    
#    print ">>> RETURNING tag %s" % ptb_tag
        
    return copy(ptb_tag)
    
def label_verb_compound(node):
    node[0].category = 'conj' if node[0].tag == 'CC' else node.category
    node[1].category = 'conj' if node[1].tag == 'CC' else node.category
    
    if node[0].tag == 'CC':
        node[0].category = 'CC'
        node[1].category = node.category
    elif node[1].tag == 'CC':
        node[1].category = 'CC'
        node[0].category = node.category
    else:
        node[0].category = node.category
        node[1].category = node.category | node.category
    
    node.kids[0] = label(node[0])
    node.kids[1] = label(node[1])
    
    return node
    
#@echo
def label(node):
    '''
    Labels the descendants of _node_ and returns _node_.
    '''
    #print "<><><> %s" % node.category
    #print "<><><> %s" % type(node.category)
    #print "<><><> %s" % (node.category is None)
    if (node.category is None):# and base_tag(node.tag) in Map:
        #print ">>> ASSIGNING CATEGORY"
        node.category = ptb_to_cat(node.tag)
        #print ">>> category is None, assigning", node.category
        
    if node.is_leaf():
        if not node.category:
            node.category = ptb_to_cat(node.tag)
        return node
        
    elif is_topicalisation(node) or is_topicalisation_without_gap(node):
        node.kids[0] = label(node[0])
        if node.count() > 1:
            node.kids[1] = label(node[1])
            
        return node
    
    elif is_apposition(node):
        if not node.category:
            node.category = ptb_to_cat(node.tag)

        node.kids[0] = label(node[0])
        if node.count() > 1:
            node.kids[1] = label(node[1])
        
        return node
        
    elif is_modification(node):
        if not node.category:
            node.category = ptb_to_cat(node.tag)
            
#        node[0].category = node.category / node.category
        node.kids[0] = label(node[0])

#        node[1].category = node.category
        node.kids[1] = label(node[1])
            
        return node
        
    elif node.count() == 1: 
        if not node.category:
            node.category = ptb_to_cat(node.tag)
        node.kids[0] = label(node[0])
        return node
        
    elif is_verb_compound(node):
        if not node.category:
            node.category = node.parent.category # VP < VRD, ...
        return label_verb_compound(node)
        
    elif is_left_absorption(node):
        return label_left_absorption(node)
    elif is_right_absorption(node):
        return label_right_absorption(node)

    elif is_predication(node):
        return label_predication(node)
    elif is_right_adjunction(node): # (:h :a), for aspect particles
        return label_right_adjunction(node)
        
    elif is_partial_coordination(node):
        if is_np_structure(node):
            return rename_category_while_labelling_with(label_partial_coordination, node, N, when=lambda category: category == NP)
        return label_partial_coordination(node)
    elif is_coordination(node):
        if is_np_structure(node):
            return rename_category_while_labelling_with(label_coordination, node, N, when=lambda category: category == NP)
        return label_coordination(node)
        
    elif is_np_structure(node):
        print "is_np_structure"
        print node

#        node.category = N
        # ret = label_np_structure(node)
        # ret.category = N
        # 
        # return ret
        return rename_category_while_labelling_with(label_np_structure, node, N, when=lambda category: category == NP)
#        return label_np_structure(node)
        
    elif is_np_internal_structure(node):
        print "is_np_internal_structure"
        print node
#        if not node.category:
#            node.category = ptb_to_cat(node.tag)
#        node.category = NP

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
                kid.category = C('conj')
            elif kid.tag.startswith('NP'):
                kid.category = P
            else:
                kid.category = ptb_to_cat(kid.tag)
                
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
        warn("Node did not match any known patterns -- assuming adjunction: %s", node.__repr__(suppress_lex=True))
        return label_adjunction(node)

def label_root(node):
    node.category = ptb_to_cat(node.tag)
    node = label(node)
    return node

class LabelNodes(Filter, OutputDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        self.outdir = outdir
        
    def accept_derivation(self, bundle):
        bundle.derivation = label_root(bundle.derivation)
        
        self.write_derivation(bundle)