import re
from copy import copy

from munge.cats.cat_defs import featureless
from munge.trees.traverse import lrp_repr
from munge.cats.nodes import BACKWARD, FORWARD
from munge.util.deco_utils import predicated
from munge.util.exceptions import MungeException

def has_tag(node, tag):
    '''Checks whether _node_ has the munge tag (not the PCTB part-of-speech) _tag_.'''
    t = node.tag
    return t[-1] == tag and t[-2] == ':'
    
def has_tags(node, tags):
    '''Checks whether _node_ has a munge tag matching any in _tags_.'''
    t = node.tag
    return t[-1] in tags and t[-2] == ':'
    
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

def replace_kid(node, old, new):
    # make sure you go through Node#__setitem__, not by modifying Node.kids directly,
    # otherwise parent pointers won't get updated 
    try:
        i = node.kids.index(old)
        node[i] = new
    except ValueError:
        raise MungeException("Tried to replace:\n\t%s\nwith:\t%s\nactual kids:\n\t%s" % (lrp_repr(old), lrp_repr(new), '\n\t'.join((lrp_repr(kid) for kid in node.kids))))
    
#      P                   P
#     / \       ->        / \
#     L  R-i              L  r-i      where -i is an optional index
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
     
def inherit_index(node, other):
    '''Gives _node_ the index that _other_ has, unless _node_ already has one, or _other_ doesn't.'''
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

@predicated
def fcomp(l, r):
    if (l.is_leaf() or r.is_leaf() or
        l.right != r.left or
        l.direction != FORWARD or l.direction != r.direction): return None

    return fake_unify(l, r, l.left / r.right)

@predicated
def bcomp(l, r):
    if (l.is_leaf() or r.is_leaf() or
        l.left != r.right or
        l.direction != BACKWARD or l.direction != r.direction): return None
        
    return fake_unify(r, l, r.left | l.right)

@predicated
def bxcomp(l, r):
    # Y/Z X\Y -> X/Z
    if (l.is_leaf() or r.is_leaf() or
        l.left != r.right or
        l.direction != FORWARD or l.direction == r.direction): return None

    return fake_unify(r, l, r.left / l.right)
    
@predicated
def bxcomp2(l, r):
    # (Y/Z)/W X\Y -> (X/Z)/W
    if not (l.is_complex() and r.is_complex() and l.left.is_complex() and
        l.left.left == r.right and
        l.direction == l.left.direction and l.direction != r.direction): return None
        
    return fake_unify(r, l, (r.left/l.left.right)/l.right)

@predicated
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
    if not cur.features: return result

    res = result
    while res.is_complex(): res = res.left
    res.features = copy(cur.features)

    return result
    
TR_FORWARD, TR_BACKWARD, TR_TOPICALISATION = 1, 2, 3
def typeraise(x, t, dir, strip_features=True):
    '''
    Performs the typeraising X -> T|(T|X).
    '''
    if strip_features:
        T, X = featureless(t), featureless(x)
    else:
        T, X = t, x

    if dir == TR_FORWARD:
        return T/(T|X)
    elif dir == TR_BACKWARD:
        return T|(T/X)
    elif dir == TR_TOPICALISATION:
        return T/(T/X)
    else:
        raise MungeException("Invalid typeraise direction.")
