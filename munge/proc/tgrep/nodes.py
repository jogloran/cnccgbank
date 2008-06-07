from munge.proc.tgrep.ops import *
from munge.util.err_utils import warn
import re

# the context simply maps identifier names to tree nodes
Context = dict

class Node(object):
    '''Represents a head node matcher (the anchor) and its sequence of constraints.'''
    def __init__(self, anchor, constraints=None):
        self.anchor = anchor
        
        if not constraints: constraints = []
        self.constraints = constraints
        
    def __repr__(self):
        return "%s%s%s" % (self.anchor, 
                           ' ' if self.constraints else '', 
                           ' '.join(str(c) for c in self.constraints))
        
    def is_satisfied_by(self, node, context=Context()):
        if self.anchor.is_satisfied_by(node, context):
            # XXX: side effects for unevaluated constraints will not be executed (due to short-circuiting)
            return all(constraint.is_satisfied_by(node, context) for constraint in self.constraints)
        return False
        
class Constraint(object):
    '''Represents a single constraint, characterised by an operator symbol and an argument node.'''
    def __init__(self, operator, rhs):
        self.operator = operator
        self.rhs = rhs
        
        self.op_func = self.get_op_func_for(self.operator)

    def get_op_func_for(self, operator):
        if operator in Operators:
            return Operators[operator]
        else:
            for regex, op_func_maker in IntArgOperators.iteritems():
                matches = re.search(regex, operator)
                if matches:
                    return op_func_maker(*matches.groups())
                if regex.search(operator): return op_func
            else:
                err('Invalid operator %s encountered.', self.operator)
        
    def __repr__(self):
        return "%s %s" % (self.operator, self.rhs)
    def is_satisfied_by(self, node, context):
        try:
            # Determine whether rhs matches the candidate node
            return self.op_func(self.rhs, node, context)
        except KeyError:
            warn("Invalid operator %s encountered.", self.operator)

        return False
        
class Negation(object):
    '''Represents the negation of a constraint.'''
    def __init__(self, inner):
        self.inner = inner
    def __repr__(self):
        return "!%s" % self.inner
    def is_satisfied_by(self, node, context):
        return not self.inner.is_satisfied_by(node, context)
        
class Alternation(object):
    '''Represents a disjunction between two constraints.'''
    def __init__(self, lhs, rhs):
        self.lhs, self.rhs = lhs, rhs
    def __repr__(self):
        return "%s | %s" % (self.lhs, self.rhs)
    def is_satisfied_by(self, node, context):
        return self.lhs.is_satisfied_by(node, context) or self.rhs.is_satisfied_by(node, context)
        
class Group(object):
    def __init__(self, node):
        self.node = node
    def __repr__(self):
        return "{%s}" % self.node
    def is_satisfied_by(self, node, context):
        return self.node.is_satisfied_by(node, context)
        
class ConstraintGroup(object):
    '''Matches when all sub-constraints are matched.'''
    def __init__(self, constraints):
        self.constraints = constraints
    def __repr__(self):
        return "[%s]" % ' '.join(str(c) for c in self.constraints)
    def is_satisfied_by(self, node, context):
        return all(constraint.is_satisfied_by(node, context) for constraint in self.constraints)
 
class Atom(object):
    '''Matches only on an exact string match.'''
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return self.value
    def is_satisfied_by(self, node, context):
        return self.value == str(node.cat)
        
class StoreAtom(object):
    '''Matches exactly what its body matches, with the side effect of capturing the matched node to a variable.'''
    def __init__(self, atom, var):
        self.atom = atom
        self.var = var
    def __repr__(self):
        return "%s=%s" % (self.atom, self.var)
    def is_satisfied_by(self, node, context):
        satisfied = self.atom.is_satisfied_by(node, context)
        if satisfied:
            context[self.var] = node
        return satisfied
        # # store into context as side effect
        # context[self.var] = self.atom
        # # TODO: Should we prevent the just-assigned variable from being used when evaluating this node?
        # return self.atom.is_satisfied_by(node, context)
        
class GetAtom(object):
    '''Matches tree nodes which are identical to the captured tree node.'''
    def __init__(self, var):
        self.var = var
    def __repr__(self):
        return "$%s" % (self.var)
    def is_satisfied_by(self, node, context):
        if self.var not in context:
            raise TgrepException('No variable %s exists in the context.')
        stored_node = context[self.var]
        #return atom.is_satisfied_by(node, context)
        # TODO: a node only matches against itself? or against something with the same label as itself?
        # XXX: This defines two nodes as equal if they are the same modulo features (which is what we often want)
        return stored_node.cat == node.cat
        
class RE(object):
    '''Matches tree nodes whose category labels satisfy a regex.'''
    def __init__(self, source):
        self.source = source
        self.regex = re.compile(source)
    def __repr__(self):
        return "/%s/" % self.source
    def is_satisfied_by(self, node, context):
        return self.regex.match(str(node.cat)) is not None

class All(object):
    '''Matches unconditionally against any tree node.'''
    def __repr__(self):
        return "*"
    def is_satisfied_by(self, node, context):
        return True

