import re
import copy
import munge.trees.traverse as traverse
from munge.util.func_utils import const_
from weakref import ref

class Node(object):
    '''Representation of a CCGbank internal node.'''
    
    __slots__ = ["cat", "head_index", "child_count", "parent", "_lch", "_rch"]
    
    # We allow lch to be None to make easier the incremental construction of Node structures in
    # the parser. Conventionally, lch can never be None.
    def __init__(self, cat, head_index, child_count, parent, lch=None, rch=None):
        '''Creates a new internal node.'''
        self.cat = cat
        self.head_index, self.child_count = head_index, child_count
        self.parent = ref(parent) if parent else None

        self._lch, self._rch = lch, rch
        
        if self._lch:
            self._lch.parent = self
        if self._rch:
            self._rch.parent = self

    def __repr__(self):
        '''Returns a (non-evaluable) string representation, a CCGbank bracketing.'''
        return (" ".join(
            ("(<T", str(self.cat), self.head_index, str(self.child_count) + ">",
             str(self.lch), str(self.rch)+' ' if self.rch else '')
        ) + ")")

    def __iter__(self):
        '''Iterates over each child of this node.'''
        yield self.lch
        if self.rch: yield self.rch

    @property
    def lch(self): return self._lch
    @lch.setter
    def lch(self, new_lch):
        if not new_lch: return
        self._lch = new_lch
        self._lch.parent = self

    @property
    def rch(self): return self._rch
    @rch.setter
    def rch(self, new_rch):
        if not new_rch: return
        self._rch = new_rch
        self._rch.parent = self

    def __eq__(self, other):
        if other is None or other.is_leaf(): return False
        
        return (self.cat == other.cat and
                self.lch == other.lch and
                self.rch == other.rch and
                self.head_index == other.head_index and
                self.child_count == other.child_count)
                
    def __ne__(self, other): return not (self == other)

    is_leaf = const_(False)
    def label_text(self): return re.escape(str(self.cat))
    
    def leaf_count(self):
        '''Returns the number of leaves under this node.'''
        count = 1 + self._lch.leaf_count()
        if self._rch: count += self._rch.leaf_count()
        
        return count
        
    def clone(self): return copy.copy(self)
    
    def text(self):
        '''Returns a list of text tokens corresponding to the leaves under this node.'''
        return traverse.text(self)

    def __getitem__(self, index):
        if index != 0 and index != 1:
            raise RuntimeError('Invalid index %d into Node %s.' % (index, self))

        return self.lch if index == 0 else self.rch

    def count(self):
        '''Returns the number of children under this node.'''
        if self.rch is None: return 1
        else: return 2
        
    @property
    def tag(self):
        return str(self.cat)

class Leaf(object):
    '''Representation of a CCGbank leaf.'''
    
    __slots__ = ["cat", "pos1", "pos2", "lex", "catfix", "parent"]
    
    def __init__(self, cat, pos1, pos2, lex, catfix, parent=None):
        '''Creates a new leaf node.'''
        self.cat = cat
        self.cat.slot.head.lex = lex
        
        self.pos1, self.pos2 = pos1, pos2
        self.lex = lex
        self.catfix = catfix
        self.parent = ref(parent) if parent else None

    def __repr__(self):
        '''Returns a (non-evaluable) string representation, a CCGbank bracketing.'''
        return " ".join(("(<L", str(self.cat), self.pos1, self.pos2, self.lex, self.catfix)) + ">)"

    def __iter__(self): raise StopIteration

    def __eq__(self, other):
        if other is None or not other.is_leaf(): return False
        
        return (self.cat == other.cat and
                self.pos1 == other.pos1 and
                self.pos2 == other.pos2 and
                self.lex == other.lex and
                self.catfix == other.catfix)
                
    def __ne__(self, other): return not (self == other)

    is_leaf = const_(True)
    leaf_count = const_(1)
    count = const_(0)
    
    def label_text(self): return """%s %s""" % (re.escape(str(self.cat)), self.lex)
    
    def clone(self): return copy.copy(self)
    
    def text(self):
        '''Returns a list of text tokens corresponding to the leaves under this node.'''
        return traverse.text(self)

    def __getitem__(self, index):
        raise NotImplementedError('Leaf has no children.')

    @property
    def tag(self):
        return str(self.cat)
