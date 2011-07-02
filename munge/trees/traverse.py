# coding: utf-8

import re
from itertools import izip, count

def ancestors(node):
    '''Iterates over the nodes on a path from the given _node_ to the root.'''
    while node.parent:
        node = node.parent
        yield node

def nodes(deriv):
    '''Preorder iterates over each node in a derivation.'''
    yield deriv
    for kid in deriv:
        for kid_node in nodes(kid):
            yield kid_node
            
def nodes_reversed(deriv):
    '''Iterates over each node in a derivation, backwards.'''
    yield deriv
    for kid in reversed(deriv):
        for kid_node in nodes_reversed(kid):
            yield kid_node

def nodes_inorder(deriv):
    '''Inorder iterates over the nodes of a binary branching derivation.'''
    is_leaf = deriv.is_leaf()
    if not is_leaf:
        for node in nodes_inorder(deriv.lch):
            yield node
    yield deriv
    if not is_leaf:
        for node in nodes_inorder(deriv.rch):
            yield node
            
def nodes_postorder(n):
    '''Given a node _n_, iterates over its nodes in post-order.'''
    if n.is_leaf():
        yield n
    else:
        for kid in nodes_postorder(n[0]): yield kid
        if n.count() > 1:
            for kid in nodes_postorder(n[1]): yield kid
        yield n

def pairs_postorder(n):
    '''Given a node _n_, iterates over pairs (l, r, p) in post-order.'''
    if not n.is_leaf():
        for v in pairs_postorder(n[0]): yield v
        if n.count() > 1:
            for v in pairs_postorder(n[1]): yield v
        yield (n[0], n[1] if n.count() > 1 else None, n)

def leaves(deriv, pred=None):
    '''Iterates from left to right over the leaves of a derivation.'''
    if deriv.is_leaf():
        if (not pred) or (pred and pred(deriv)): yield deriv
    else:
        for kid in deriv:
            for kid_node in leaves(kid, pred):
                yield kid_node
                
def leaves_reversed(deriv, pred=None):
    '''Iterates from right to left over the leaves of a derivation.'''
    if deriv.is_leaf():
        if (not pred) or (pred and pred(deriv)): yield deriv
    else:
        for kid in reversed(deriv):
            for kid_node in leaves_reversed(kid, pred):
                yield kid_node

def text(deriv, pred=lambda e: True):
    '''Returns a list of the tokens at the leaves of a derivation.'''
    return [node.lex for node in leaves(deriv) if pred(node)]
    
def is_ignored(node, ignoring_quotes=True):
    '''Is true for a PTB node which corresponds to no CCGbank node (traces or quote symbols).'''
    # We check that the POS tag is not ':' to exclude the erroneous analysis in 21:61(24) 
    # (see munge.proc.quote.quotify spans())
    return (re.match(r'-?NONE-?', node.tag) or
            (ignoring_quotes and
               ((re.match(r'^``?$', node.lex) or
                (node.tag not in ("POS", ":") and re.match(r"^''?$", node.lex)))) or
                (node.lex in ("“", "”"))))
    
def text_without_quotes_or_traces(deriv, pred=lambda e: True):
    '''Returns a list of the text under this node, ignoring quote symbols or traces.'''
    return text(deriv, lambda e: pred(e) and not is_ignored(e, ignoring_quotes=True))
    
def text_without_traces(deriv, pred=lambda e: True):
    '''Returns a list of the text under this node, ignoring traces.'''
    return text(deriv, lambda e: pred(e) and not is_ignored(e, ignoring_quotes=False))
    
def text_in_span(deriv, begin, end):
    '''Returns a subset of the text under this node, as specified by a pair of indices
(0 would be the leftmost leaf under this node).'''
    for cur_index, leaf in enumerate(leaves(deriv)):
        if begin <= cur_index < end:
            yield leaf.lex
        elif cur_index >= end:
            return
            
def tag_and_lex(node):
    return "|".join((node.tag, node.lex))

def tag_and_text_under(node):
    return "%s|(%s)" % (node.tag, ' '.join(node.text()))
    
def lrp_repr(node):
    try:
        if node.is_leaf():
            return tag_and_lex(node)
        else:
            return "%s (%s)" % (node.tag, " ".join(tag_and_text_under(x) for x in node))
    except AttributeError:
        return repr(node)
    
# Assumes that the second argument is a leaf.
def get_index_of_leaf(deriv, leaf):
    for cur_index, candidate_leaf in enumerate(leaves(deriv)):
        if leaf is candidate_leaf: return cur_index
    return None

def get_leaf(derivation, token_index, direction="forwards"):
    '''Retrieves the nth leaf under this node, either counting from the leftmost or rightmost
leaf under this node.'''
    cur_index = 0

    if direction == "forwards":
        for leaf in leaves(derivation):
            if cur_index == token_index: return leaf
            cur_index += 1

    else:
        for leaf in leaves_reversed(derivation):
            if cur_index == token_index: return leaf
            cur_index += 1

    return None
