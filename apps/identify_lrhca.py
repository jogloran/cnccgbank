import re

from munge.proc.cn.count import last_nonpunct_kid

def base_tag(tag):
    if re.match(r'-.+-$', tag): return tag
    
    #print "base_tag: %s ->" % tag,
    tag = re.sub(r':.+$', '', tag)
    tag = re.sub(r'-.+$', '', tag)
    #print tag
    return tag

def is_left_absorption(node):
    return node[0].is_leaf() and node[0].tag == 'PU' and base_tag(node[1].tag) == base_tag(node.tag)
    
def is_right_absorption(node):
    # TODO: refactor into one method
    return node[1].is_leaf() and node[1].tag == 'PU' and base_tag(node[0].tag) == base_tag(node.tag)

def is_np_sbj(node):
    return re.match(r'NP(-\w+)*-SBJ', node.tag) is not None

def is_vp(node):
    return node.tag == 'VP'

def is_predication(node):
    return (node.tag.startswith('IP') and 
            is_np_sbj(node[0]) and 
            is_vp(node[1]))

def is_head_final(node):
    return last_nonpunct_kid(node).tag.endswith(':h')

def is_head_initial(node):
    return node[0].tag.endswith(':h')

def is_adjunction(node):
    return node[0].tag.endswith(':a')
    
def is_right_adjunction(node):
    return node[1].tag.endswith(':a')

def is_coordination(node):
    return node[0].tag.endswith(':c')
    
def is_apposition(node):
    return node[0].tag.endswith(':A')

def is_np_internal_structure(node):
    return node.tag.startswith('NP') and node.count() > 1 and all(kid.tag in ('NN', 'PU') for kid in node)
    
def is_apposition(node):
    return node[0].tag.endswith(':A')
    
def is_modification(node):
    return node[0].tag.endswith(':m')