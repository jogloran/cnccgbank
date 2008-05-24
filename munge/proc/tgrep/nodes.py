from munge.proc.tgrep.ops import *
from munge.util.err_utils import warn
import re

class Node(object):
    def __init__(self, anchor, constraints=None):
        self.anchor = anchor
        
        if not constraints: constraints = []
        self.constraints = constraints
        
    def __repr__(self):
        return "%s%s%s" % (self.anchor, ' ' if self.constraints else '', ' '.join(str(c) for c in self.constraints))
        
    def is_satisfied_by(self, node):
        if self.anchor.is_satisfied_by(node):
            return all(constraint.is_satisfied_by(node) for constraint in self.constraints)
        return False
        
class Constraint(object):
    def __init__(self, operator, rhs):
        self.operator = operator
        self.rhs = rhs
    def __repr__(self):
        return "%s %s" % (self.operator, self.rhs)
    def is_satisfied_by(self, node):
        try:
            op_func = Operators[self.operator]
            # Determine whether rhs matches the candidate node
            return op_func(self.rhs, node)
        except KeyError:
            warn("Invalid operator %s encountered.", self.operator)

        return False
        
class Group(object):
    def __init__(self, node):
        self.node = node
    def __repr__(self):
        return "{%s}" % self.node
    def is_satisfied_by(self, node):
        return self.node.is_satisfied_by(node)

class Atom(object):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return self.value
    def is_satisfied_by(self, node):
        return self.value == str(node.cat)
        
class RE(object):
    def __init__(self, source):
        self.source = source
        self.regex = re.compile(source)
    def __repr__(self):
        return "/%s/" % self.source
    def is_satisfied_by(self, node):
        return self.regex.match(str(node.cat)) is not None
