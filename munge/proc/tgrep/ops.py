from munge.trees.traverse import nodes
from munge.util.deco_utils import cast_to
from munge.trees.traverse import get_index_of_leaf, get_leaf, leaves, ancestors
from itertools import islice

def IsParentOf(candidate, node, context):
    if node.is_leaf(): return False
    if node.count() == 1:
        return candidate.is_satisfied_by(node[0], context)
    elif node.count() == 2:
        return (candidate.is_satisfied_by(node[0], context) or
                candidate.is_satisfied_by(node[1], context))
    return any(candidate.is_satisfied_by(child, context) for child in node)

# A << B => B is a node under A
# node <- A
# ask: out of all nodes under A, does 'candidate' match any of them?
def Dominates(candidate, node, context):
    if node.is_leaf(): return False
    
    # to exclude _node_ itself (which is first in the sequence):
    internal_nodes = islice(nodes(node), 1, None)
    
    return any(candidate.is_satisfied_by(internal_node, context) for internal_node in internal_nodes)

def IsChildOf(candidate, node, context):
    if node.parent is None: return False
    return candidate.is_satisfied_by(node.parent, context)

def IsDominatedBy(candidate, node, context):
    if node.parent is None: return False
    return any(candidate.is_satisfied_by(ancestor, context) for ancestor in ancestors(node))
    
def get_root(node):
    while node.parent: node = node.parent
    return node

def ImmediatelyPrecedes(candidate, node, context):
    if not node.is_leaf(): return False
    
    # does a node which matches 'candidate' occur immediately before _node_?
    root = get_root(node)
    
    node_index = get_index_of_leaf(root, node)
    
    successor = get_leaf(root, node_index+1)
    if not successor: return False
    if candidate.is_satisfied_by(successor, context): return True
    
    return False

# A . B => B comes after A
# node <- A
# out of all nodes after A, is B one of them?
def Precedes(candidate, node, context):
    if not node.is_leaf(): return False
    
    root = get_root(node)
    
    node_index = get_index_of_leaf(root, node)
    
    for successor in islice(leaves(root), node_index+1):
        if candidate.is_satisfied_by(successor, context): 
            return True
            
    return False
    
def IsSiblingOf(candidate, node, context):
    if node.parent is None: return False
    
    for kid in node.parent:
        if kid is node: continue
        if candidate.is_satisfied_by(kid, context): return True
    
    return False
    
def not_implemented(*args):
    raise NotImplementedError('not implemented')

IsSiblingOfAndImmediatelyPrecedes = not_implemented
IsSiblingOfAndPrecedes = not_implemented

def LeftChildOf(candidate, node, context):
    if node.is_leaf(): return False
    return candidate.is_satisfied_by(node[0], context)

def RightChildOf(candidate, node, context):
    if node.is_leaf(): return False
    return node.count() > 1 and candidate.is_satisfied_by(node[1], context)
    
def AllChildrenOf(candidate, node, context):
    if node.is_leaf(): return False
    return all(candidate.is_satisfied_by(kid, context) for kid in node)

@cast_to(int)
def IsNthChildOf(n):
    def _IsNthChildOf(candidate, node, context):
        if not 1 <= n <= node.count(): return False
        # value is 1-indexed, while child indexing in Nodes is 0-indexed
        return candidate.is_satisfied_by(node[n-1], context)
    return _IsNthChildOf
    
@cast_to(int)
def ChildCount(n):
    def _ChildCount(candidate, node, context):
        return node.count() == n
    return _ChildCount

def And(candidate, node, context):
    return candidate.is_satisfied_by(node, context)

Operators = {
    '<': IsParentOf,
    '<<': Dominates,
    '<1': LeftChildOf,
    '<2': RightChildOf,
    '<%': AllChildrenOf,
    '>': IsChildOf,
    '>>': IsDominatedBy,
    '.': ImmediatelyPrecedes,
    '..': Precedes,
    '$': IsSiblingOf,
    '$.': IsSiblingOfAndImmediatelyPrecedes,
    '$..': IsSiblingOfAndPrecedes,
    '&': And,
}

IntArgOperators = {
    r'<(\d+)': IsNthChildOf,
    r'\#<(\d+)': ChildCount
}
