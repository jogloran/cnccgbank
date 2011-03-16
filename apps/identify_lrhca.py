import re
#from echo import echo

from munge.trees.traverse import leaves
from apps.identify_pos import *
from apps.util.config import config
from munge.util.func_utils import satisfies_any

def _base_tag(tag, strip_cptb_tag=True, strip_tag=True):
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
    
try:
    from pressplit import base_tag
except ImportError:
    base_tag = _base_tag

def last_nonpunct_kid(node):
    kid, index = get_nonpunct_kid(node)
    return kid
    
def get_nonpunct_element(e, get_last=True):
    if get_last:
        for i, kid in enumerate(reversed(e)):
            if not kid.tag.startswith('PU'): return kid, len(e) - i - 1
    else:
        for i, kid in enumerate(e):
            if not kid.tag.startswith('PU'): return kid, i
            
    return None, None
    
def get_nonpunct_kid(node, get_last=True):
    if node.is_leaf(): return None, None
    return get_nonpunct_element(node.kids, get_last=get_last)

if config.restrictive_absorption:
    def is_left_absorption(node):
        return node[0].is_leaf() and node[0].tag == 'PU' and (
            (base_tag(node[1].tag) == base_tag(node.tag)) or
            (satisfies_any(has_verbal_tag, is_verb_compound)(node[1]) and node.tag.startswith('VP')) or
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
            # 1:50(7)
            (has_verbal_tag(node[1]) and node.tag.startswith('IP')) or
            # 5:95(38)
            (node[1].tag.startswith('CP') and node.tag.startswith('IP')) or
            # 10:48(85)
            (node[1].tag.startswith('IP') and node.tag.startswith('CP')) or
            # 11:26(81), 11:13(131) buggy sentences were breaking tokenisation
            (node[1].tag.startswith('NP') and (node.tag.startswith('PRN') or node.tag.startswith('FRAG'))) )
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
            (satisfies_any(has_verbal_tag, is_verb_compound)(node[0]) and node.tag.startswith('VP')) or
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
            # after PRO trace is shrunk (10:12(33))
            (node[0].tag.startswith('VP') and node.tag.startswith('IP')) or
            # v this mess took me half an hour to debug (29:93(15))
            (node[0].tag.startswith('PP') and node.tag.startswith('IP')) or
            (node[0].tag.startswith('NP') and node.tag.startswith('VP')) or
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
    return (
        node[0].is_leaf() and (node[0].tag.startswith('CC') or node[0].tag == 'PU') and #and node[1].tag.endswith(':c') and \
    # To handle serial comma-like constructions, which manifest as
    # XP PU CC XP, we want the CC, and not the PU, to be the operator,
    # despite the PU being higher in the tree:
        (node[1].is_leaf() or not node[1][0].tag.startswith('CC'))
    )

# NP NP[conj] -> NP
def is_coordination(node):
    return node[0].tag.endswith(':c') or node[1].tag.endswith(':c')

def is_partial_ucp(node):
    return ((node[0].is_leaf() and (node[0].tag.startswith('CC') or node[0].tag == 'PU') and node[1].tag.endswith(':C')) and
        base_tag(node.tag) != base_tag(node[1].tag))

def is_ucp(node):
    # TODO: The test for node[1].tag != PU is to prevent a rare mis-analysis of punctuation in a UCP being
    # identified as a conjunct. Need to investigate further
    return node[0].tag.endswith(':C') and node[1].tag != 'PU'

def is_np_internal_structure(node):
    return (node.tag.startswith('NP') and 
            all(kid.tag.endswith(':n') 
             or kid.tag.endswith(':N') 
             or kid.tag in NominalCategories
             or kid.tag in ('PU', 'CC')
             or kid.tag.startswith('JJ')
             or kid.tag.endswith(':&') for kid in leaves(node)))
    
def is_S_NP_apposition(node):
    return node.tag.startswith('NP') and 
    # IP-APP < *pro* VP may be reduced to VP-APP by binarise
        (node[0].tag.startswith('IP-APP') or node[0].tag.startswith('VP-APP')) and (
        node[1].tag.startswith('NP') or has_noun_tag(node[1]))
    
def is_np_structure(node):
    # These tags are attested NP modifiers
    # rule out NP-PRD as NP structure (0:88(15))
    return node.tag.startswith('NP') and all( #and not node.tag.startswith('NP-PRD')) and all(
        (any(kid.tag.startswith(cat) for cat in NominalCategories)) or 
        kid.tag.startswith('ADJP') or 
        kid.tag.startswith('QP') or
        kid.tag.startswith('DP') or
        kid.tag.startswith('CP') or
        kid.tag.startswith('DNP') or
        kid.tag.startswith('ADVP') or
        kid.tag.startswith('IP') or
        kid.tag.startswith('JJ') or # JJ is in here because ADJP < JJ may have been shrunk already
        kid.tag.startswith('LCP') or
        kid.tag.startswith('CLP') or # 0:57(12) reduced M
        kid.tag.startswith('PP') or
        kid.tag in ("PU", "CC") or # CC for underspecified NP (27:24(3))
        kid.tag.startswith('NP') or
        kid.tag.startswith('WHNP') or # 9:30(13)
        kid.tag.startswith('FLR') or # ignore FLR
        kid.tag.startswith('SP') or # ignore SP
        kid.tag.endswith(':p') for kid in node)
    
def is_apposition(node):
    return any(kid.tag.endswith(':A') for kid in node)
    
def is_argument_cluster(node):
    return all(kid.tag.endswith(':@') for kid in node)
    
def is_modification(node):
    return node[0].tag.endswith(':m')

def is_topicalisation(node):
    return node[0].tag.endswith(':t')
    
def is_topicalisation_without_gap(node):
    return node[0].tag.endswith(':T')
    
def is_etc(node):
    return node.count() > 1 and node[1].tag.endswith(':&')
    
def is_prn(node):
    return node.tag.endswith(':p')
