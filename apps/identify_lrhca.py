import re
#from echo import echo

from apps.cn.fix_utils import has_tag, has_tags, base_tag
from munge.trees.traverse import leaves
from apps.identify_pos import *
from apps.util.config import config
from munge.util.func_utils import satisfies_any

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

def is_left_absorption(node):
    return node[0].is_leaf() and node[0].tag == "PU"

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
    return (has_tag(lnpk, 'h') or has_tag(node[0], 'l')) if lnpk else False

def is_head_initial(node):
    return has_tag(node[0], 'h') or has_tag(node[1], 'r')

def is_adjunction(node):
    return has_tag(node[0], 'a')

def is_right_adjunction(node):
    return has_tags(node[1], 'ap')

# conj NP -> NP[conj]
def is_partial_coordination(node):
    return (
        node[0].is_leaf() and (node[0].tag.startswith('CC') or node[0].tag in ('PU', 'CSC')) and #and has_tag(node[1], 'c') and \
    # To handle serial comma-like constructions, which manifest as
    # XP PU CC XP, we want the CC, and not the PU, to be the operator,
    # despite the PU being higher in the tree:
        (node[1].is_leaf() or not node[1][0].tag.startswith('CC'))
    )

# NP NP[conj] -> NP
def is_coordination(node):
    return has_tag(node[0], 'c') or has_tag(node[1], 'c')

def is_partial_ucp(node):
    return ((node[0].is_leaf() and (node[0].tag.startswith('CC') or node[0].tag == 'PU') and has_tag(node[1], 'C')) and
        base_tag(node.tag) != base_tag(node[1].tag))

def is_ucp(node):
    # TODO: The test for node[1].tag != PU is to prevent a rare mis-analysis of punctuation in a UCP being
    # identified as a conjunct. Need to investigate further
    return has_tag(node[0], 'C') and node[1].tag != 'PU'

def is_np_internal_structure(node):
    # rule out things already tagged explicitly as coordination by tag.py
    if any(has_tags(kid, 'cC') for kid in node): return False
    
    return (node.tag.startswith('NP') and
            all(has_tags(kid, 'nN')
             or any(kid.tag.startswith(tag) for tag in NominalCategories)
             or kid.tag in ('PU', 'CC')
             or kid.tag.startswith('JJ')
             or kid.tag.startswith('CD')
             or kid.tag.startswith('OD')
             or has_tag(kid, '&') for kid in leaves(node)))

def is_S_NP_apposition(node):
    # IP-APP < *pro* VP may be reduced to VP-APP by binarise, or
    # IP-APP < *PRO* VV (shrunk already by binarise unary shrink) to VV-APP 7:17(7)
    # IP-APP < *PRO* VA -- we need to match against VA-APP too 10:4(3)
    return node.tag.startswith('NP') and \
        (node[0].tag.startswith('IP-APP') or node[0].tag.startswith('VP-APP') or node[0].tag.startswith('VV-APP') or node[0].tag.startswith('VA-APP') or
         node[0].tag.startswith('VCD-APP') or node[0].tag.startswith('VSB-APP') or node[0].tag.startswith('VRD-APP')) and (
        node[1].tag.startswith('NP') or has_noun_tag(node[1]))

def is_np_structure(node):
    # These tags are attested NP modifiers
    # rule out NP-PRD as NP structure (0:88(15))
    
    # rule out things already tagged explicitly as coordination by tag.py
    if any(has_tags(kid, 'cC') for kid in node): return False
    
    return node.tag.startswith('NP') and all(
        (any(kid.tag.startswith(cat) for cat in NominalCategories)) or
        kid.tag.startswith('ADJP') or
        kid.tag.startswith('QP') or kid.tag.startswith('CD') or
        kid.tag.startswith('DP') or kid.tag.startswith('DT') or
        # 24:98(3)
        kid.tag.startswith('PN') or
        kid.tag.startswith('CP') or
        kid.tag.startswith('DNP') or
        kid.tag.startswith('ADVP') or kid.tag.startswith('AD') or
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
        has_tag(kid, 'p') for kid in node)

def is_apposition(node):
    return any(has_tag(kid, 'A') for kid in node)

def is_argument_cluster(node):
    return all(has_tag(kid, '@') for kid in node)

def is_modification(node):
    return has_tag(node[0], 'm')

def is_topicalisation(node):
    return has_tag(node[0], 't')

def is_topicalisation_without_gap(node):
    return has_tag(node[0], 'T')

def is_etc(node):
    return node.count() > 1 and has_tag(node[1], '&')

def is_prn(node):
    return has_tag(node, 'p')
