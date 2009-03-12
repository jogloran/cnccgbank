import re
from echo import echo

from munge.proc.cn.count import last_nonpunct_kid
from munge.trees.traverse import leaves

def base_tag(tag):
    if re.match(r'-.+-$', tag): return tag
    
    tag = re.sub(r':.+$', '', tag)
    tag = re.sub(r'-.+$', '', tag)
    
    return tag
    
VerbalCategories = ('VV', 'VA', 'VC', 'VE')
    
def is_verb_compound(node):
    return all((has_verbal_tag(kid) or kid.tag == 'CC') for kid in leaves(node))
    
def has_verbal_tag(node):
    return any(node.tag.startswith(cand) for cand in VerbalCategories)
    
NominalCategories = ('NN', 'NR', 'NT')

def has_noun_tag(node):
    return any(node.tag.startswith(cand) for cand in NominalCategories)

def is_left_absorption(node):
    return node[0].is_leaf() and node[0].tag == 'PU' and base_tag(node[1].tag) == base_tag(node.tag)
    
def is_right_absorption(node):
    # TODO: refactor into one method
    return node[1].is_leaf() and node[1].tag == 'PU' and (
        base_tag(node[0].tag) == base_tag(node.tag) or
        # HACK: special case, it seems VV PU -> VP is attested (31:42(2)),
        #       and VC PU -> VP (3:23(4)).
        # it seems we get NN PU -> NP as well (10:2(17))
        (has_verbal_tag(node[0]) and node.tag.startswith('VP')) or
        (has_noun_tag(node[0]) and node.tag.startswith('NP')))

def is_np_sbj(node):
#    return re.match(r'NP(-\w+)*-SBJ', node.tag) is not None
    return re.search(r'-SBJ', node.tag) is not None

def is_vp(node):
    return node.tag.startswith('VP')

# TODO: this definition is too restrictive
def is_predication(node):
#    return (node.tag.startswith('IP') and 
#            is_np_sbj(node[0]) and 
#            is_vp(node[1]))
    return (node.tag.startswith('IP') and
        any(is_np_sbj(kid) for kid in node) and
        any(is_vp(kid) for kid in node))

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
    
# def is_np_internal_structure(node):
#     return node.tag.startswith('NP') and node.count() > 1 and (
#         all(kid.tag in ('NN', 'NR', 'NT', 'PU') for kid in leaves(node)) or 
#         all(kid.tag.startswith('NP') for kid in node))

def is_np_internal_structure(node):
    return node.tag.startswith('NP') and all(kid.tag.endswith(':n') or kid.tag.endswith(':N') or kid.tag in ('PU', 'CC') for kid in node)
    
def is_apposition(node):
    return node[0].tag.endswith(':A')
    
def is_modification(node):
    return node[0].tag.endswith(':m')

def is_topicalisation(node):
    return node[0].tag.endswith(':t')
    
def is_topicalisation_without_gap(node):
    return node[0].tag.endswith(':T')