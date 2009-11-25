import re
#from echo import echo

from apps.cn.tag import last_nonpunct_kid
from munge.trees.traverse import leaves
from apps.identify_pos import *

# 
def base_tag(tag):
    '''
    Strips any CPTB tags (e.g. NP[-PRD]), as well as our tags (e.g. NP[:r]). Traces are returned
    unmodified.
    '''
    # -NONE-
    if len(tag) >= 3 and (tag[0] == tag[-1] == "-"): return tag

    # Remove our tags
    colon_index = tag.find(":")
    if colon_index != -1: tag = tag[:colon_index]
    
    # Remove CPTB tags
    dash_index = tag.find("-")
    if dash_index != -1: tag = tag[:dash_index]
    
    return tag

def is_left_absorption(node):
    return node[0].is_leaf() and node[0].tag == 'PU' and (
        (base_tag(node[1].tag) == base_tag(node.tag)) or
        (has_verbal_tag(node[1]) and node.tag.startswith('VP')) or
        (has_noun_tag(node[1]) and node.tag.startswith('NP')) or
        # 10:3(7)
        (node[1].tag.startswith('CP-Q') and node.tag.startswith('IP')) or
        # 3:10(18) nearly all of these seem to be phrase-final P(yinwei)
        (node[1].tag.startswith('PP') and node.tag.startswith('IP')) or
        # 5:95(38)
        (node[1].tag.startswith('CP') and node.tag.startswith('IP')))
    
def is_right_absorption(node):
    # TODO: refactor into one method
    # are these special cases? or are they just a consequence of binarisation?
    # if you have IP < NP , VP you will get IP < , VP after binarisation
    return node[1].is_leaf() and node[1].tag == 'PU' and (
        (base_tag(node[0].tag) == base_tag(node.tag)) or
        # HACK: special case, it seems VV PU -> VP is attested (31:42(2)),
        #       and VC PU -> VP (3:23(4)).
        # it seems we get NN PU -> NP as well (10:2(17))
        (has_verbal_tag(node[0]) and node.tag.startswith('VP')) or
        (has_noun_tag(node[0]) and node.tag.startswith('NP')) or
        # 8:38(22)
        (node[0].tag == 'P' and node.tag.startswith('PP')) or
        # LC PU -> LCP (6:47(5))
        (node[0].tag.startswith('LC') and node.tag.startswith('LCP')) or
        # PU IP DEC PU -> CP (1:85(9))
        (node[0].tag.startswith("DEC") and node.tag.startswith('CP')) or
        # CP < IP PU (6:72(13))
        (node[0].tag.startswith("IP") and node.tag.startswith('CP')))

def is_xp_sbj(node):
    return re.search(r'-SBJ', node.tag) is not None

def is_vp(node):
    return node.tag.startswith('VP')

# TODO: this definition is too restrictive: Chinese allows non VP predicates
def is_predication(node):
    return (node.tag.startswith('IP') and
        any(is_xp_sbj(kid) for kid in node) and
        any(is_vp(kid) or has_verbal_tag(kid) for kid in node))

def is_head_final(node):
    lnpk = last_nonpunct_kid(node)
    return (lnpk.tag.endswith(':h') or node[0].tag.endswith(':l')) if lnpk else False

def is_head_initial(node):
    return node[0].tag.endswith(':h') or node[1].tag.endswith(':r')

def is_adjunction(node):
    return node[0].tag.endswith(':a')
    
def is_right_adjunction(node):
    return node[1].tag.endswith(':a')
        
# conj NP -> NP[conj]
def is_partial_coordination(node):
    return node[0].is_leaf() and (node[0].tag.startswith('CC') or node[0].tag == 'PU') and node[1].tag.endswith(':c')

def is_coordination(node):
    return node[0].tag.endswith(':c') or node[1].tag.endswith(':c')

def is_np_internal_structure(node):
    return (node.tag.startswith('NP') and 
            all(kid.tag.endswith(':n') 
             or kid.tag.endswith(':N') 
             or kid.tag in NominalCategories
             or kid.tag in ('PU', 'CC')
             or kid.tag.startswith('JJ')
             or kid.tag.endswith(':&') for kid in leaves(node)))
    
def is_np_structure(node):
    # These tags are attested NP modifiers
    return node.tag.startswith('NP') and all(
        (any(kid.tag.startswith(cat) for cat in NominalCategories)) or 
        kid.tag.startswith('ADJP') or 
        kid.tag.startswith('QP') or
        kid.tag.startswith('DP') or
        kid.tag.startswith('CP') or
        kid.tag.startswith('DNP') or
        kid.tag.startswith('ADVP') or
        kid.tag.startswith('IP') or
        kid.tag.startswith('JJ') or 
        kid.tag == "PU" or
        kid.tag.startswith('NP') for kid in node)
    
def is_apposition(node):
    return node[0].tag.endswith(':A')
    
def is_modification(node):
    return node[0].tag.endswith(':m')

def is_topicalisation(node):
    return node[0].tag.endswith(':t')
    
def is_topicalisation_without_gap(node):
    return node[0].tag.endswith(':T')
    
def is_etc(node):
    return node[1].tag.endswith(':&')