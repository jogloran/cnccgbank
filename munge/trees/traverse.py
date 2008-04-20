import re
from itertools import izip, count

def nodes(deriv):
    '''Preorder iterates over each node in a derivation.'''
    yield deriv
    for kid in deriv:
        for kid_node in nodes(kid):
            yield kid_node
            
def nodes_reversed(deriv):
    '''Iterates over each node in a derivation, backwards.'''
    yield deriv
    for kid in reversed(list(deriv)):
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

def leaves(deriv):
    '''Iterates from left to right over the leaves of a derivation.'''
    if deriv.is_leaf(): yield deriv
    else:
        for kid in deriv:
            for kid_node in leaves(kid):
                yield kid_node
                
def leaves_reversed(deriv):
    '''Iterates from right to left over the leaves of a derivation.'''
    if deriv.is_leaf(): yield deriv
    else:
        for kid in reversed(list(deriv)):
            for kid_node in leaves_reversed(kid):
                yield kid_node

def text(deriv, pred=lambda e: True):
    '''Returns a list of the tokens at the leaves of a derivation.'''
    return [node.lex for node in leaves(deriv) if pred(node)]
    
def is_ignored(node, ignoring_quotes=True):
    return (re.match(r'-?NONE-?', node.tag) or
            (ignoring_quotes and
                (re.match(r'^``?$', node.lex) or
                (node.tag != "POS" and re.match(r"^''?", node.lex)))))
    
def text_without_quotes_or_traces(deriv):
    return text(deriv, lambda e: not is_ignored(e, ignoring_quotes=True))
    
def text_without_traces(deriv):
    return text(deriv, lambda e: not is_ignored(e, ignoring_quotes=False))
    
def text_in_span(deriv, begin, end):
    for leaf, cur_index in izip(leaves(deriv), count()):
        if begin <= cur_index < end:
            yield leaf.lex
        elif cur_index >= end:
            return

def get_leaf(derivation, token_index, direction="forwards"):
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