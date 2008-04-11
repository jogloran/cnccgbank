from copy import copy
from munge.util.exceptions import CatParseException
import re

ShowModes = True

BACKWARD, FORWARD = range(2)
APPLY, ALL, COMP, NULL = range(4)

class AtomicCategory(object):
    '''Represents an atomic category (one without a directional slash).'''
    def __init__(self, cat, features=None):
        self.cat = cat
        self.features = features or []

    def feature_repr(self):
        '''Returns the concatenation of each feature in this category's feature set.'''
        return ''.join("[%s]" % feature for feature in self.features)

    def __repr__(self, first=True):
        '''A (non-evaluable) representation of this category. Ignores its first argument
        so it can be treated uniformly with ComplexCategory.'''
        return self.cat + self.feature_repr()
        
    @property
    def label(self): return None

    # AtomicCategory is immutable
    def clone(self):
        '''Returns a copy of this category. AtomicCategory is intended to be immutable,
        so this returns the category itself.'''
        return self

    def has_feature(self, feature):
        '''Determines whether the given feature is present in this category's feature set.'''
        return feature in self.features

    def equal_respecting_features(self, other):
        '''Determines if this category is equal to another, taking into account their features.'''
        if not isinstance(other, AtomicCategory): return False
        return (self == other and
                self.features == other.features)

    def __eq__(self, other):
        '''Determines if this category is equal to another, without inspecting any features.'''
        if not isinstance(other, AtomicCategory): return False
        return self.cat == other.cat

    def labelled(self, index=0): return index
    def is_labelled(self): return False

    def slash_count(self): return 0
    
    def nested_compound_categories(self): return []

    def is_leaf(self): return True
    def label_text(self): return re.escape(self.cat)

    def is_compound(self): return not self.is_leaf()

class ComplexCategory(object):
    '''Represents a complex category.'''
    
    # Index i into mode_symbols references the mode with integer representation i.
    mode_symbols = "*.@-"
    def get_mode_symbol(self, mode_index):
        if not mode_index: return '' # for when cat.mode is None
        
        try:
            return self.mode_symbols[mode_index]
        except (IndexError, TypeError):
            raise CatParseException('Invalid mode index %s.' % mode_index)

    def __init__(self, left, direction, right, mode=None, features=None, label=None):
        self.left, self.direction, self.right = left, direction, right
        self.mode = mode
        self.features = features or []
        self.label = label

        self.slash = "\\" if self.direction == BACKWARD else "/"

    def feature_repr(self):
        '''Returns the concatenation of each feature in this category's feature set.'''
        return ''.join("[%s]" % feature for feature in self.features)

    def __repr__(self, first=True):
        '''A (non-evaluable) representation of this category.'''
        return "%(open)s%(lch)s%(slash)s%(mode)s%(rch)s%(close)s%(feats)s" % {
            'open': "" if first else "(",
            'lch': self.left.__repr__(False),
            'slash': self.slash,
            'mode': self.get_mode_symbol(self.mode) if ShowModes else "",
            'rch': self.right.__repr__(False),
            'close': "" if first else ")",
            'feats': self.feature_repr()
        }

    def clone(self):
        '''Returns a copy of this category.'''
        return ComplexCategory(self.left.clone(),
                               self.direction, 
                               self.right and self.right.clone(),
                               self.mode, copy(self.features))
                               
    def has_feature(self, feat):
        '''Determines whether the given feature is present in this category's feature set.'''
        return (feat in self.features or
                self.left.has_feature(feat) or
                self.right.has_feature(feat))

    def equal_respecting_features(self, other):
        '''Determines if this category is equal to another, taking into account their features.'''
        if not isinstance(other, ComplexCategory): return False

        return (self.direction == other.direction and 
                self.features == other.features and
                self.left.equal_respecting_features(other.left) and
                self.right.equal_respecting_features(other.right))

    def __eq__(self, other):
        '''Determines if this category is equal to another, without inspecting any features.'''
        if not isinstance(other, ComplexCategory): return False

        return (self.direction == other.direction and
                self.left == other.left and
                self.right == other.right)

    def labelled(self, index=0):
        self.label = index
        index += 1 # the current node gets the label _index_
        index = self.left.labelled(index)
        index = self.right.labelled(index)
        return index

    def is_labelled(self):
        return self.label or any(kid.is_labelled() for kid in self)

    def slash_count(self):
        return 1 + self.left.slash_count() + self.right.slash_count()

    def __iter__(self):
        '''Iterates over the result, then the argument of this category.'''
        yield self.left
        yield self.right
        
    def nested_compound_categories(self):
        return ([self] + 
                 self.left.nested_compound_categories() + 
                 self.right.nested_compound_categories())    

    def is_leaf(self): return False
    def label_text(self): return re.escape(self.slash)

    def is_compound(self): return not self.is_leaf()
