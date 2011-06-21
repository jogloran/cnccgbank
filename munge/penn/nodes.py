from munge.trees.traverse import text_without_traces, text_without_quotes_or_traces, leaves
from munge.util.func_utils import const_
import re

class Node(object):
    '''Representation of a PTB internal node.'''
    
    __slots__ = ['tag', 'kids', 'parent']
    
    def __init__(self, tag, kids, parent=None):
        self.tag = tag
        self.kids = kids
        
        self.parent = parent
        
    @property
    def cat(self):
        return self.tag

    def __repr__(self, first=True, suppress_lex=False):
        return "%s(%s %s)%s" % ("(" if first else "", 
                                self.tag, 
                                ' '.join(kid.__repr__(False, suppress_lex) for kid in self.kids), 
                                ")" if first else "")

    def __iter__(self):
        return self.kids.__iter__()
    def __reversed__(self):
        return reversed(self.kids)
        
    def leaf_count(self):
        return len(leaves(self))

    def count(self):
        return len(self.kids)
    __len__ = count
    __nonzero__ = const_(True)
    is_leaf = const_(False)
    
    def label_text(self): return re.escape(self.tag)
    
    def text(self, with_quotes=True):
        return (text_without_traces if with_quotes else text_without_quotes_or_traces)(self)

    def __getitem__(self, index):
        try:
            n = len(self.kids)
            if not (-n <= index < n): 
                raise RuntimeError("Invalid index %d into Node %s." % (index, self))
            return self.kids[index]
        except TypeError:
            return self.kids[index.start:index.stop]
            
    def __setitem__(self, index, value):
        try:
            n = len(self.kids)
            if not (-n <= index < n): 
                raise RuntimeError("Invalid index %d into Node %s." % (index, self))
            self.kids[index] = value
            value.parent = self
        except TypeError:
            self.kids[index.start:index.stop] = value
            for node in value:
                value.parent = self
                
    def __delitem__(self, index):
        self.kids.__delitem__(index)

    def __eq__(self, other):
        return (not other.is_leaf()) and self.tag == other.tag and self.kids == other.kids
    def __ne__(self, other): return not (self == other)
    
class Leaf(object):
    '''Representation of a PTB leaf.'''
    
    __slots__ = ['tag', 'lex', 'parent']

    def __init__(self, tag, lex, parent):
        self.tag = tag
        self.lex = lex
        
        self.parent = parent
        
    @property
    def cat(self):
        return self.tag

    def __repr__(self, first=True, suppress_lex=False):
        return ("%s(%s%s)%s" %
            ("(" if first else '',
            self.tag, '' if suppress_lex else (' ' + self.lex),
            ")" if first else ''))
            
    def __iter__(self): raise StopIteration
    __reversed__ = __iter__

    count = const_(0)
    __len__ = count
    __nonzero__ = const_(True)
    is_leaf = const_(True)
    
    def leaf_count(self): return 1

    def label_text(self): return "%s '%s'" % (re.escape(self.tag), self.lex)
    
    def text(self, with_quotes=True):
        return (text_without_traces if with_quotes else text_without_traces_or_quotes)(self)

    def not_implemented(self, *args):
        raise NotImplementedError('Leaf has no children.')
    __getitem__ = __setitem__ = not_implemented
        
    def __eq__(self, other):
        return other.is_leaf() and self.tag == other.tag and self.lex == other.lex
    def __ne__(self, other): return not (self == other)
