import munge.cats.nodes as B
from apps.util.config import config

class Head(object):
    '''A Head represents an assigned lexical item.'''
    def __init__(self, lex=None, filler=None):
        self.lex = lex
        self.filler = None
    
    __repr__ = lambda self: str(self.lex) or "?"

class Slot(object):
    '''A Slot is a mapping from a variable name to a Head.'''
    def __init__(self, var, head_lex=None):
        self.var = var        
        self._head = Head(head_lex)
        
    @property
    def head(self): return self._head
    @head.setter
    def head(self, v): self._head = v
        
    def is_filled(self):
        return self.head.lex is not None
        
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
        
class AtomicCategory(B.AtomicCategory):
    '''An AtomicCategory augmented with a Slot field.'''
    def __init__(self, *args, **kwargs):
        var, value = kwargs.pop('var', '?'), kwargs.pop('value', None)
        
        B.AtomicCategory.__init__(self, *args, **kwargs)
        self.slot = Slot(var, value)
        
    if config.show_vars:
        def __repr__(self, *args, **kwargs):
            r = B.AtomicCategory.__repr__(self, *args, **kwargs)
            if kwargs.get('suppress_vars', False): return r
                
            if self.slot:
                r += repr(self.slot)
            return r
        
if config.curly_vars:
    def bracket_category(s):
        return "(" + s + ")"
else:
    def bracket_category(s):
        return "[" + s + "]"
    
class ComplexCategory(B.ComplexCategory):
    '''A ComplexCategory augmented with a Slot field.'''
    def __init__(self, *args, **kwargs):
        var, value = kwargs.pop('var', '?'), kwargs.pop('value', None)
        
        B.ComplexCategory.__init__(self, *args, **kwargs)
        self.slot = Slot(var, value)
    
    if config.show_vars:
        def __repr__(self, *args, **kwargs):
            r = B.ComplexCategory.__repr__(self, *args, **kwargs)
            if kwargs.get('suppress_vars', False): return r
                    
            if self.slot.var:
                if kwargs.get('first', True):
                    r = bracket_category(r)
        
            r += repr(self.slot)
        
            return r
        
