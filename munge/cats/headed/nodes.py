# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import munge.cats.nodes as B
from munge.util.config import config
from copy import copy

class Head(object):
    '''A Head represents an assigned lexical item.'''
    def __init__(self, lex=None, filler=None):
        self._lex = lex
        self.filler = None

    @property
    def lex(self): return self._lex
    @lex.setter
    def lex(self, lex): self._lex = lex
        
    def __hash__(self):
        if isinstance(self._lex, list): return hash(frozenset(self._lex))
        else: return hash(self._lex)
    def __eq__(self, other):
        return (self._lex == other._lex) and (self.filler is not None)
    
    __repr__ = lambda self: "<|%s|>" % (str(self.lex) or "?")

class Slot(object):
    '''A Slot is a mapping from a variable name to a Head.'''
    def __init__(self, var, head_lex=None):
        self.var = var        
        self._head = Head(head_lex)
        
        self.dependers = set()
        self.dependers.add( self )
        
    @property
    def head(self): 
        return self._head
        
    def unify_heads(self, other):
        assert isinstance(other, Slot), "unify_heads is an operation between two Slots."
        self.dependers |= other.dependers
        
        for dep in self.dependers:
            dep._head = other._head
            dep.dependers = self.dependers
        
    def is_filled(self):
        return self.head.lex is not None
        
    # problem: sometimes two slots have the same var name and same head, but are distinct slots
    # the problem goes away when var names are uniquified
    def __hash__(self):
        return hash(id(self))
#        return hash(self.var) ^ hash(self._head)
    def __eq__(self, other):
        return self is other
#        return self.var == other.var and self._head == other._head
        
    if config.curly_vars:
        def __repr__(self):
            head = ('=' + self.head.lex) if self.head.lex else ''
            return "{" + self.var + head + "}"
    else:
        def __repr__(self):
            if not self.head.lex: head = None
            elif isinstance(self.head.lex, list): 
                head = '<' + ', '.join(self.head.lex) + '>'
            else: head = self.head.lex
            
            return self.var.lower() + (("=" + head) if head else '')
            
class Aliased(object):
    def __init__(self, alias):
        self.alias = alias
        
class AtomicCategory(B.AtomicCategory, Aliased):
    '''An AtomicCategory augmented with a Slot field.'''
    NoVariableSentinel = '?'

    def __init__(self, *args, **kwargs):
        var, value = kwargs.pop('var', self.NoVariableSentinel), kwargs.pop('value', None)
        alias = kwargs.pop('alias', None)
        
        B.AtomicCategory.__init__(self, *args, **kwargs)
        Aliased.__init__(self, alias)
        
        self.slot = Slot(var, value)
        
    if config.show_vars:
        def __repr__(self, *args, **kwargs):
            r = B.AtomicCategory.__repr__(self, *args, **kwargs)
            
            if not kwargs.get('suppress_vars', False):                
                if self.slot:
                    r += repr(self.slot)
                
            if self.alias and not kwargs.get('suppress_alias', False):
                r += '~'+self.alias
                
            return r
    else:
        def __repr__(self, *args, **kwargs):
            r = B.AtomicCategory.__repr__(self, *args, **kwargs)
            if self.alias and not kwargs.get('suppress_alias', False):
                r += '~'+self.alias
            return r
    
    def equal_respecting_features_and_alias(self, other):
        return B.AtomicCategory.equal_respecting_features(self, other) and self.alias == other.alias
            
    def __hash__(self):
        return B.AtomicCategory.__hash__(self) ^ hash(self.slot) ^ hash(self.alias)

    def clone_with(self, features=None, slot=None):
        ret = AtomicCategory(self.cat, 
                             features if features else copy(self.features))
        ret.slot = slot or self.slot
        return ret
        
if config.curly_vars:
    def bracket_category(s):
        return "(" + s + ")"
else:
    def bracket_category(s):
        return "[" + s + "]"
    
class ComplexCategory(B.ComplexCategory, Aliased):
    '''A ComplexCategory augmented with a Slot field.'''
    def __init__(self, *args, **kwargs):
        var, value = kwargs.pop('var', '?'), kwargs.pop('value', None)
        alias = kwargs.pop('alias', None)
        
        B.ComplexCategory.__init__(self, *args, **kwargs)
        Aliased.__init__(self, alias)
        
        self.slot = Slot(var, value)
    
    if config.show_vars:
        def __repr__(self, *args, **kwargs):
            r = B.ComplexCategory.__repr__(self, *args, **kwargs)
            if not kwargs.get('suppress_vars', False):
                if self.slot.var:
                    if kwargs.get('first', True):
                        r = bracket_category(r)
        
                r += repr(self.slot)
            
            if self.alias and not kwargs.get('suppress_alias', False):
                r += '~'+self.alias
        
            return r
    else:
        def __repr__(self, *args, **kwargs):
            r = B.ComplexCategory.__repr__(self, *args, **kwargs)
            if self.alias and not kwargs.get('suppress_alias', False):
                r += '~'+self.alias
            return r
            
    def equal_respecting_features_and_alias(self, other):
        return B.ComplexCategory.equal_respecting_features(self, other) and self.alias == other.alias

    def clone_with(self, left=None, direction=None, right=None, features=None, slot=None):
        ret = ComplexCategory(left if left else self._left.clone(),
                              direction if direction else self.direction,
                              right if right else self._right.clone(),
                              self.mode, 
                              features if features else copy(self.features))
        ret.slot = slot or self.slot
        return ret

    def clone(self):
        ret = ComplexCategory(self._left.clone(),
                               self.direction, 
                               self._right and self._right.clone(),
                               self.mode, copy(self.features))
        ret.slot = self.slot
        return ret

    def __hash__(self):
        return B.ComplexCategory.__hash__(self) ^ hash(self.slot) ^ hash(self.alias)
