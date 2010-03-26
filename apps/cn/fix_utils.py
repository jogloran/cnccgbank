import re
from copy import copy

from munge.cats.cat_defs import featureless
from munge.trees.traverse import lrp_repr
from apps.identify_lrhca import base_tag
from munge.cats.nodes import BACKWARD, FORWARD
from munge.util.err_utils import debug

def replace_kid(node, old, new):
    # make sure you go through Node#__setitem__, not by modifying Node.kids directly,
    # otherwise parent pointers won't get updated 
    try:
        i = node.kids.index(old)
        node[i] = new
    except ValueError:
        raise Exception("Tried to replace:\n\t%s\nwith:\t%s\nactual kids:\n\t%s" % (lrp_repr(old), lrp_repr(new), '\n\t'.join((lrp_repr(kid) for kid in node.kids))))
    
#      P                   P
#     / \       ->        / \
#     L  R                L  r
#       / \
#       l  r
def shrink_left(node, parent):
    if parent:
        kid = node[1]
        inherit_index(kid, node)
        replace_kid(parent, node, kid)
        return kid
    else: # is root
        return node[1]
     
from apps.util.echo import echo   
def inherit_index(node, other):
    matches = re.search(r'(-\d+)', other.tag)
    if matches:
        if not re.search(r'-\d+', node.tag):
            till_tag, after_tag = node.tag.split(':')
            index_to_inherit = matches.group(1)
            node.tag = till_tag + index_to_inherit + ":" + after_tag
    
def inherit_tag(node, other, strip_marker=False):
    # node = IP:h other = CP-APP:a
    # node = IP:h-APP:a
    '''Gives _node_ the tag that _other_ has, unless _node_ already has one, or _other_ doesn't.'''
    if strip_marker: node.tag = base_tag(node.tag, strip_cptb_tag=False)
    
    if other.tag.rfind('-') != -1 and node.tag.rfind(':') == -1:
        node.tag += other.tag[other.tag.rfind('-'):]
    elif other.tag.rfind(':') != -1 and node.tag.rfind(':') == -1:
        node.tag += other.tag[other.tag.rfind(':'):]

def fcomp(l, r):
    if (l.is_leaf() or r.is_leaf() or
        l.right != r.left or
        l.direction != FORWARD or l.direction != r.direction): return None

    return fake_unify(l, r, l.left / r.right)

def bcomp(l, r, when=True):
    if not when: return None
    if (l.is_leaf() or r.is_leaf() or
        l.left != r.right or
        l.direction != BACKWARD or l.direction != r.direction): return None
        
    debug('creating category %s', r.left | l.right)
    return fake_unify(l, r, r.left | l.right)

def bxcomp(l, r):
    # Y/Z X\Y -> X/Z
    if (l.is_leaf() or r.is_leaf() or
        l.left != r.right or
        l.direction != FORWARD or l.direction == r.direction): return None

    return fake_unify(l, r, r.left / l.right)

def fxcomp(l, r):
    if (l.is_leaf() or r.is_leaf() or
        l.right != r.left or
        l.direction != FORWARD or r.direction == l.direction): return None

    return fake_unify(l, r, l.left | r.right)
    
def fake_unify(l, r, result):
    # Fake unification onto result category
    # 1. get inner-most result category from R
    # 2. give its features to L's result category
    # 3. ???
    # 4. Profit!!!

    result = result.clone()

    cur = r
    while cur.is_complex(): cur = cur.left

    res = result
    while res.is_complex(): res = res.left
    res.features = copy(cur.features)

    return result
    
TR_FORWARD, TR_BACKWARD, TR_TOPICALISATION = 1, 2, 3
def typeraise(x, t, dir):
    '''
    Performs the typeraising X -> T|(T|X).
    '''
    T, X = featureless(t), featureless(x)

    if dir == TR_FORWARD:
        return T/(T|X)
    elif dir == TR_BACKWARD:
        return T|(T/X)
    elif dir == TR_TOPICALISATION:
        return T/(T/X)
    else:
        raise RuntimeException, "Invalid typeraise direction."
