from munge.trees.traverse import nodes

def IsParentOf(candidate, node):
    if node.is_leaf(): return False
    return any(candidate.is_satisfied_by(child) for child in node)

def Dominates(candidate, node):
    return any(candidate.is_satisfied_by(internal_node) for internal_node in nodes(node))

def IsChildOf(candidate, node):
    return candidate.is_satisfied_by(node.parent)

def IsDominatedBy(candidate, node):
    pass

def ImmediatelyPrecedes(candidate, node):
    pass

def Precedes(candidate, node):
    pass

def IsSiblingOf(candidate, node):
    if node.parent is None: return False
    
    was_left_child = node.parent.lch is node
    if was_left_child:
        if node.parent.rch is not None:
            return candidate.is_satisfied_by(node.parent.rch)
    else:
        return candidate.is_satisfied_by(node.parent.lch)
    return False

def IsSiblingOfAndImmediatelyPrecedes(candidate, node):
    pass

def IsSiblingOfAndPrecedes(candidate, node):
    pass

def LeftChildOf(candidate, node):
    if node.is_leaf(): return False
    return candidate.is_satisfied_by(node.lch)

def RightChildOf(candidate, node):
    if node.is_leaf(): return False
    return node.rch is not None and candidate.is_satisfied_by(node.rch)

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

