from copy import copy, deepcopy
from munge.util.exceptions import CatParseException
from munge.util.func_utils import const_
from apps.util.config import config

import re

BACKWARD, FORWARD = range(2)
APPLY, ALL, COMP, NULL = range(4)

ShowModes = config.use_modes

class Featured(object):
    '''Represents an object with a _features_ field. The class this is mixed into must provide
a method clone_with(features) which returns a copy of itself with the given features added.'''
    def __init__(self, features=None):
        self.features = features or []
        
    def feature_repr(self):
        '''Returns the concatenation of each feature in this category's feature set.'''
        n = len(self.features)
        if n == 0: return ''
        elif n == 1: return "[" +  self.features[0] + "]"
        else: return ''.join("[%s]" % feature for feature in self.features)
        
    def has_feature(self, feature):
        '''Determines whether the given feature is present in this category's feature set.'''
        return feature in self.features
        
    def clone_adding_feature(self, feature):
        '''Returns a copy of this category with the given feature appended.'''
        return self.clone_with(features=(list(self.features) + [feature]))

class AtomicCategory(Featured):
    '''Represents an atomic category (one without a directional slash).'''
    def __init__(self, cat, features=None):
        Featured.__init__(self, features)
        self.cat = cat
        
    def __hash__(self):
        return hash(self.cat)

    def __repr__(self, first=True, show_modes=ShowModes, **kwargs):
        '''A (non-evaluable) representation of this category. Ignores both its arguments
        so it can be treated uniformly with ComplexCategory.'''
        return self.cat + self.feature_repr()
        
    @property
    def label(self): return None

    # AtomicCategory is immutable
    def clone(self):
        '''Returns a copy of this category. AtomicCategory is intended to be immutable,
        so this returns the category itself.'''
        return copy(self)
        
    def clone_with(self, features=None):
        '''Returns a copy of this category with the given feature set.'''
        return AtomicCategory(self.cat, features if features else copy(self.features))

    def equal_respecting_features(self, other):
        '''Determines if this category is equal to another, taking into account their features.'''
        if not other.is_leaf(): return False
        
        return (self == other and
                self.features == other.features)

    def __eq__(self, other):
        '''Determines if this category is equal to another, without inspecting any features.'''
        if not other.is_leaf(): return False
        return self.cat == other.cat
        
    def __ne__(self, other): return not (self == other)

    def labelled(self, index=0): return index
    postorder_labelled = labelled
    def parg_labelled(self, index=1): return index
    def is_labelled(self): return False

    slash_count = const_(0)
    
    def nested_compound_categories(self): yield self

    def label_text(self): return re.escape(self.cat)

    is_leaf = const_(True)
    is_complex = const_(False)
    
    def __iter__(self):
        yield self
    
    def __or__(self, right):
        '''Constructs the complex category (self \ right).'''
        return ComplexCategory(self, BACKWARD, right)
        
    def __div__(self, right):
        '''Constructs the complex category (self / right).'''
        return ComplexCategory(self, FORWARD, right)

class ComplexCategory(Featured):
    '''Represents a complex category.'''
    
    # Index i into mode_symbols references the mode with integer representation i.
    mode_symbols = "*.@-"
    @staticmethod
    def get_mode_symbol(mode_index):
        if mode_index is None: return '' # for when cat.mode is None
        
        try:
            return ComplexCategory.mode_symbols[mode_index]
        except (IndexError, TypeError):
            raise CatParseException('Invalid mode index %s.' % mode_index)
            
    def __init__(self, left, direction, right, mode=None, features=None, label=None):
        Featured.__init__(self, features)
        
        self._left, self.direction, self._right = left, direction, right
        self.mode = mode
        self.label = label

        self.slash = "\\" if self.direction == BACKWARD else "/"
        
    @property
    def left(self):
        return self._left
    @property
    def right(self):
        return self._right

    def __repr__(self, first=True, show_modes=ShowModes, show_label=False, **kwargs):
        '''A (non-evaluable) representation of this category.'''
        # ensure that we display (X/Y)[f] and not X/Y[f]
        if self.features: first = False
        
        bits = []
        if not first: bits.append('(')
        bits.append(self._left.__repr__(first=False, show_modes=show_modes, show_label=show_label, **kwargs))
        bits.append(self.slash)
        if show_label and self.label is not None: bits.append(str(self.label))
        if show_modes: bits.append(ComplexCategory.get_mode_symbol(self.mode))
        bits.append(self._right.__repr__(first=False, show_modes=show_modes, show_label=show_label, **kwargs))
        if not first: bits.append(')')
        bits.append(self.feature_repr())
        
        return ''.join(bits)

    def clone(self):
        '''Returns a copy of this category.'''
        return ComplexCategory(self._left.clone(),
                               self.direction, 
                               self._right and self._right.clone(),
                               self.mode, copy(self.features))
                  
    def clone_with(self, left=None, direction=None, right=None, features=None):
        return ComplexCategory(left if left else self._left.clone(),
                               direction if direction else self.direction,
                               right if right else self._right.clone(),
                               self.mode, 
                               features if features else copy(self.features))
                               
    def equal_respecting_features(self, other):
        '''Determines if this category is equal to another, taking into account their features.'''
#        if self is other: return True
        if not other.is_complex(): return False

        return (self.direction == other.direction and 
                self.features == other.features and
                self._left.equal_respecting_features(other.left) and
                self._right.equal_respecting_features(other.right))

    def __eq__(self, other):
        '''Determines if this category is equal to another, without inspecting any features.'''
#        if self is other: return True
        if not other.is_complex(): return False

        return (self.direction == other.direction and
                self._left == other.left and
                self._right == other.right)
                
    def __ne__(self, other): return not (self == other)
    
    def __hash__(self):
        return hash(self.direction) ^ hash(self._left) ^ hash(self._right)

    def labelled(self, index=0):
        '''Labels this category in-place. Labelling attaches indices to each slash of this
category in a pre-order traversal of the category tree.'''
        self.label = index
        index += 1 # the current node gets the label _index_
        index = self._left.labelled(index)
        index = self._right.labelled(index)
        return index
        
    def postorder_labelled(self, index=0):
        index = self._left.postorder_labelled(index)
        self.label = index
        index += 1
        index = self._right.postorder_labelled(index)
        return index
        
    def parg_labelled(self, index=1):
        index = self._left.parg_labelled(index)
        self.label = index
        index += 1
        return index

    def is_labelled(self):
        '''Determines whether this category is labelled.'''
        return self.label or any(kid.is_labelled() for kid in self)

    def slash_count(self):
        '''Returns the number of slashes in this category.'''
        return 1 + self._left.slash_count() + self._right.slash_count()

    def __iter__(self):
        '''Iterates over the result, then the argument of this category.'''
        yield self._left
        yield self._right
        
    def slashes(self):
        '''For each slash of this compound category, yields a tuple of the category containing that slash
and its labelled index.'''
        yield (self, self.label)
        
        for child in (self._left, self._right):
            if child.is_complex():
                for (node, slash_index) in child.slashes(): 
                    yield (node, slash_index)
                        
    def nested_compound_categories(self):
        '''Iterates over each sub-category of this category.'''
        yield self
        for cat in self._left.nested_compound_categories(): yield cat
        for cat in self._right.nested_compound_categories(): yield cat

    def label_text(self): return re.escape(self.slash)

    is_leaf = const_(False)
    is_complex = const_(True)
    
    def __or__(self, right):
        '''Constructs the complex category (self \ right).'''
        return ComplexCategory(self, BACKWARD, right)
        
    def __div__(self, right):
        '''Constructs the complex category (self / right).'''
        return ComplexCategory(self, FORWARD, right)

if __name__ == '__main__':
    from munge.cats.parse import parse_category
    for cat, lab in {
            '(A/B)/C': '(A/1B)/2C',
            '(A/(B/D))/C': '(A/1(B/D))/2C',
            '((A/B)/D)/C': '((A/1B)/2D)/3C',
            'A/(B/C)': 'A/1(B/C)'
    }.iteritems():
        c = parse_category(cat)
        c.parg_labelled()
        print c.__repr__(show_label=True)
        assert c.__repr__(show_label=True) == lab
