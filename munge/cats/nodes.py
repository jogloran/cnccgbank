from copy import copy, deepcopy
from munge.util.exceptions import CatParseException
from apps.util.config import config

import re

BACKWARD, FORWARD = range(2)
APPLY, ALL, COMP, NULL = range(4)

ShowModes = config.use_modes

class Featured(object):
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
        
    # def add_feature(self, feature):
    #     # TODO: switch this over to a set
    #     # TODO: this makes atomiccategory mutable
    #     if feature not in self.features:
    #         self.features.append(feature)
    #     return self
    #     
    def clone_adding_feature(self, feature):
        return self.clone_with(features=(list(self.features) + [feature]))

class AtomicCategory(Featured):
    '''Represents an atomic category (one without a directional slash).'''
    def __init__(self, cat, features=None):
        Featured.__init__(self, features)
        self.cat = cat
        
    def __hash__(self):
        return hash(repr(self))

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
        return AtomicCategory(self.cat, features if features else copy(self.features))

    def equal_respecting_features(self, other):
        '''Determines if this category is equal to another, taking into account their features.'''
#        if self is other: return True
        if not other.is_leaf(): return False
        
        return (self == other and
                self.features == other.features)

    def __eq__(self, other):
        '''Determines if this category is equal to another, without inspecting any features.'''
#        if self is other: return True
        if not other.is_leaf(): return False
        return self.cat == other.cat
        
    def __ne__(self, other): return not (self == other)

    def labelled(self, index=0): return index
    def is_labelled(self): return False

    def slash_count(self): return 0
    
    def nested_compound_categories(self): yield self

    def is_leaf(self): return True
    def label_text(self): return re.escape(self.cat)

    def is_complex(self): return not self.is_leaf()
    
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
            
    def __hash__(self):
        return hash(repr(self))

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

    def __repr__(self, first=True, show_modes=ShowModes, **kwargs):
        '''A (non-evaluable) representation of this category.'''
        # ensure that we display (X/Y)[f] and not X/Y[f]
        if self.features: first = False
        
        return "%(open)s%(lch)s%(slash)s%(mode)s%(rch)s%(close)s%(feats)s" % {
            'open': "" if first else "(",
            'lch': self._left.__repr__(first=False, show_modes=show_modes),
            'slash': self.slash,
          #  'label': self.label if self.is_labelled() else "",
            'mode': ComplexCategory.get_mode_symbol(self.mode) if show_modes else "",
            'rch': self._right.__repr__(first=False, show_modes=show_modes),
            'close': "" if first else ")",
            'feats': self.feature_repr()
        }

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

    def labelled(self, index=0):
        '''Labels this category in-place. Labelling attaches indices to each slash of this
category in a pre-order traversal of the category tree.'''
        self.label = index
        index += 1 # the current node gets the label _index_
        index = self._left.labelled(index)
        index = self._right.labelled(index)
        return index

    def is_labelled(self):
        '''Determines whether this category is labelled.'''
        return self.label or any(kid.is_labelled() for kid in self)

    def slash_count(self):
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
        yield self
        for cat in self._left.nested_compound_categories(): yield cat
        for cat in self._right.nested_compound_categories(): yield cat

    def is_leaf(self): return False
    def label_text(self): return re.escape(self.slash)

    def is_complex(self): return not self.is_leaf()
    
    def __or__(self, right):
        '''Constructs the complex category (self \ right).'''
        return ComplexCategory(self, BACKWARD, right)
        
    def __div__(self, right):
        '''Constructs the complex category (self / right).'''
        return ComplexCategory(self, FORWARD, right)
