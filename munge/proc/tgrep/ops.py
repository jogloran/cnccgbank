from munge.trees.traverse import nodes
from munge.util.deco_utils import cast_to

def IsParentOf(candidate, node, context):
    if node.is_leaf(): return False
    return any(candidate.is_satisfied_by(child, context) for child in node)

def Dominates(candidate, node, context):
    return any(candidate.is_satisfied_by(internal_node, context) for internal_node in nodes(node))

def IsChildOf(candidate, node, context):
    if node.parent is None: return False

    return candidate.is_satisfied_by(node.parent, context)

def IsDominatedBy(candidate, node, context):
    pass

def ImmediatelyPrecedes(candidate, node, context):
    pass

def Precedes(candidate, node, context):
    pass

# def IsSiblingOf(candidate, node, context):
#     if node.parent is None: return False
#     
#     was_left_child = node.parent.lch is node
#     if was_left_child:
#         if node.parent.rch is not None:
#             return candidate.is_satisfied_by(node.parent.rch, context)
#     else:
#         return candidate.is_satisfied_by(node.parent.lch, context)
#     return False
    
def IsSiblingOf(candidate, node, context):
    if node.parent is None: return False
    
    for kid in node.parent:
        if kid is node: continue
        if candidate.is_satisfied_by(kid, context): return True
    
    return False
    

def IsSiblingOfAndImmediatelyPrecedes(candidate, node, context):
    pass

def IsSiblingOfAndPrecedes(candidate, node, context):
    pass

def LeftChildOf(candidate, node, context):
    if node.is_leaf(): return False
    return candidate.is_satisfied_by(node.lch, context)

def RightChildOf(candidate, node, context):
    if node.is_leaf(): return False
    return node.rch is not None and candidate.is_satisfied_by(node.rch, context)

@cast_to(int)
def IsNthChildOf(n):
    # TODO: Handle n out of bounds
    def _IsNthChildOf(candidate, node, context):
        if not 1 <= n <= node.count(): return False
        # value is 1-indexed, while child indexing in Nodes is 0-indexed
        return candidate.is_satisfied_by(node[n-1], context)
    return _IsNthChildOf

Operators = {
    '<': IsParentOf,
    '<<': Dominates,
    '<1': LeftChildOf,
    '<2': RightChildOf,
    '>': IsChildOf,
    '>>': IsDominatedBy,
    '.': ImmediatelyPrecedes,
    '..': Precedes,
    '$': IsSiblingOf,
    '$.': IsSiblingOfAndImmediatelyPrecedes,
    '$..': IsSiblingOfAndPrecedes
}

IntArgOperators = {
    r'<(\d+)': IsNthChildOf
}
