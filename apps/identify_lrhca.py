import re
#from echo import echo

from apps.cn.tag import last_nonpunct_kid
from munge.trees.traverse import leaves
from apps.identify_pos import *
from apps.util.config import config

# 
def base_tag(tag, strip_cptb_tag=True, strip_tag=True):
    '''
    Strips any CPTB tags (e.g. NP[-PRD]), as well as our tags (e.g. NP[:r]). Traces are returned
    unmodified.
    '''
    # -NONE-
    if len(tag) >= 3 and (tag[0] == tag[-1] == "-"): return tag

    # Remove our tags
    if strip_tag:
        colon_index = tag.find(":")
        if colon_index != -1: tag = tag[:colon_index]
    
    # Remove CPTB tags
    if strip_cptb_tag:
        dash_index = tag.find("-")
        if dash_index != -1: tag = tag[:dash_index]
    
    return tag
    
if config.restrictive_absorption:
    def is_left_absorption(node):
        return node[0].is_leaf() and node[0].tag == 'PU' and (
            (base_tag(node[1].tag) == base_tag(node.tag)) or
            (has_verbal_tag(node[1]) and node.tag.startswith('VP')) or
            (has_noun_tag(node[1]) and node.tag.startswith('NP')) or
            # 10:3(7)
            (node[1].tag.startswith('CP-Q') and node.tag.startswith('IP')) or
            # 3:10(18) nearly all of these seem to be phrase-final P(yinwei)
            (node[1].tag.startswith('PP') and node.tag.startswith('IP')) or
            # 21:36(4) VP final P(yinwei)
            (node[1].tag.startswith('PP') and node.tag.startswith('VP')) or
            # 10:55(34), 10:50(39)
            (node[1].tag.startswith('NP') and node.tag.startswith('IP')) or
            # 10:28(38)
            (node[1].tag.startswith('VP') and node.tag.startswith('IP')) or
            # 5:95(38)
            (node[1].tag.startswith('CP') and node.tag.startswith('IP')) or
            # 10:48(85)
            (node[1].tag.startswith('IP') and node.tag.startswith('CP')))
else:
    def is_left_absorption(node):
        return node[0].is_leaf() and node[0].tag == "PU"
    
if config.restrictive_absorption:
    def is_right_absorption(node):
        # TODO: refactor into one method
        # are these special cases? or are they just a consequence of binarisation?
        # if you have IP < NP , VP you will get IP < , VP after binarisation
        return node[1].is_leaf() and node[1].tag == 'PU' and (
            (base_tag(node[0].tag) == base_tag(node.tag)) or
            # HACK: special case, it seems VV PU -> VP is attested (31:42(2)),
            #       and VC PU -> VP (3:23(4)).
            # it seems we get NN PU -> NP as well (10:2(17))
            ( (has_verbal_tag(node[0]) or is_verb_compound(node[0])) and node.tag.startswith('VP')) or
            (has_noun_tag(node[0]) and node.tag.startswith('NP')) or
            # 8:38(22)
            (node[0].tag == 'P' and node.tag.startswith('PP')) or
            # LC PU -> LCP (6:47(5))
            (node[0].tag.startswith('LC') and node.tag.startswith('LCP')) or
            # PU IP DEC PU -> CP (1:85(9))
            (node[0].tag.startswith("DEC") and node.tag.startswith('CP')) or
            # 2:12(3)
            (node[0].tag.startswith("DEG") and node.tag.startswith('DNP')) or
            # CP < IP PU (6:72(13))
            (node[0].tag.startswith("IP") and node.tag.startswith('CP')) or
            (node[0].tag.startswith('IP') and node.tag.startswith('NP')) or
            # parentheticals
            (node.tag.startswith('PRN')))
else:
    def is_right_absorption(node):
        return node[1].is_leaf() and node[1].tag == "PU"

def is_xp_sbj(node):
    return node.tag.find('-SBJ') != -1

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
    return node[1].tag.endswith(':a') or node[1].tag.endswith(':p')
        
# conj NP -> NP[conj]
def is_partial_coordination(node):
    return node[0].is_leaf() and (node[0].tag.startswith('CC') or node[0].tag == 'PU') and node[1].tag.endswith(':c')

def is_coordination(node):
    return node[0].tag.endswith(':c') or node[1].tag.endswith(':c')

def is_partial_ucp(node):
    return ((node[0].is_leaf() and (node[0].tag.startswith('CC') or node[0].tag == 'PU') and node[1].tag.endswith(':C')) and
        base_tag(node.tag) != base_tag(node[1].tag))

def is_ucp(node):
    return node[0].tag.endswith(':C') or node[1].tag.endswith(':C')
    # if node[0].tag.endswith(':C'):
    #     return base_tag(node[0].tag) != base_tag(node.tag)
    # elif node[1].tag.endswith(':C'):
    #     return base_tag(node[1].tag) != base_tag(node.tag)
    #     
    # return False

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
    
def is_prn(node):
    return node.tag.endswith(':p')