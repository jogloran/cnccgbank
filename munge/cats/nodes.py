from copy import copy
from munge.util.exceptions import CatParseException
from exthash import bernstein_hash
import re

BACKWARD, FORWARD = range(2)
APPLY, ALL, COMP, NULL = range(4)

class AtomicCategory(object):
    '''Represents an atomic category (one without a directional slash).'''
    def __init__(self, cat, features=None):
        self.cat = cat
        self.features = features or []
        self.hash = self.rehash()

    def feature_repr(self):
        '''Returns the concatenation of each feature in this category's feature set.'''
        return ''.join("[%s]" % feature for feature in self.features)

    def __repr__(self, first=True, show_modes=True, show_features=True):
        '''A (non-evaluable) representation of this category. Ignores both its arguments
        so it can be treated uniformly with ComplexCategory.'''
        return self.cat + (self.feature_repr() if show_features else "")
        
    def rehash(self):
        self.hash = bernstein_hash(self.__repr__(show_modes=False, show_features=False))
        return self.hash
        
    def __hash__(self):
        return self.hash
        
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
#        if self is other: return True
        if not other.is_leaf(): return False
        
        return (self == other and
                self.features == other.features)

    def __eq__(self, other):
        '''Determines if this category is equal to another, without inspecting any features.'''
#        if self is other: return True
        if not other.is_leaf(): return False
        if hash(self) != hash(other): return False
        return self.cat == other.cat

    def labelled(self, index=0): return index
    def is_labelled(self): return False

    def slash_count(self): return 0
    
    def nested_compound_categories(self): return []

    def is_leaf(self): return True
    def label_text(self): return re.escape(self.cat)

    def is_compound(self): return not self.is_leaf()
    
    def __or__(self, right):
        '''Constructs the complex category (self \ right).'''
        return ComplexCategory(self, BACKWARD, right)
        
    def __div__(self, right):
        '''Constructs the complex category (self / right).'''
        return ComplexCategory(self, FORWARD, right)

class ComplexCategory(object):
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
        self.left_, self.direction_, self.right_ = left, direction, right
        self.mode_ = mode
        self.features_ = features or []
        self.label = label

        self.slash = "\\" if self.direction == BACKWARD else "/"
        
        self.hash = self.rehash()
        
    def rehash(self):
        self.hash = bernstein_hash(self.__repr__(show_modes=False, show_features=False))
        return self.hash
        
    def __hash__(self):
        return self.hash
        
    def get_left(self): return self.left_
    def set_left(self, v):
        self.left_ = v
        self.rehash()
        return self.left_
    left = property(get_left, set_left)
    
    def get_right(self): return self.right_
    def set_right(self, v):
        self.right_ = v
        self.rehash()
        return self.right_
    right = property(get_right, set_right)
    
    def get_direction(self): return self.direction_
    def set_direction(self, v):
        self.direction_ = v
        self.rehash()
        return self.direction_
    direction = property(get_direction, set_direction)
    
    def get_mode(self): return self.mode_
    def set_mode(self, v):
        self.mode_ = v
        self.rehash()
        return self.mode_
    mode = property(get_mode, set_mode)
    
    def get_features(self): return self.features_
    def set_features(self, v):
        self.features_ = v
        self.rehash()
        return self.features_
    features = property(get_features, set_features)

    def feature_repr(self):
        '''Returns the concatenation of each feature in this category's feature set.'''
        return ''.join("[%s]" % feature for feature in self.features)

    def __repr__(self, first=True, show_modes=True, show_features=True):
        '''A (non-evaluable) representation of this category.'''
        return "%(open)s%(lch)s%(slash)s%(mode)s%(rch)s%(close)s%(feats)s" % {
            'open': "" if first else "(",
            'lch': self.left.__repr__(False, show_modes, show_features),
            'slash': self.slash,
          #  'label': self.label if self.is_labelled() else "",
            'mode': ComplexCategory.get_mode_symbol(self.mode) if show_modes else "",
            'rch': self.right.__repr__(False, show_modes, show_features),
            'close': "" if first else ")",
            'feats': self.feature_repr() if show_features else ""
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
#        if self is other: return True
        if not other.is_compound(): return False

        return (self.direction == other.direction and 
                self.features == other.features and
                self.left.equal_respecting_features(other.left) and
                self.right.equal_respecting_features(other.right))

    def __eq__(self, other):
        '''Determines if this category is equal to another, without inspecting any features.'''
#        if self is other: return True
        if not other.is_compound(): return False
        if hash(self) != hash(other): return False
        return (self.direction == other.direction and
                self.left == other.left and
                self.right == other.right)

    def labelled(self, index=0):
        '''Labels this category in-place. Labelling attaches indices to each slash of this
category in a pre-order traversal of the category tree. This function returns the smallest
unassigned index.'''
        self.label = index
        index += 1 # the current node gets the label _index_
        index = self.left.labelled(index)
        index = self.right.labelled(index)
        return index

    def is_labelled(self):
        '''Determines whether this category is labelled.'''
        return self.label or any(kid.is_labelled() for kid in self)

    def slash_count(self):
        return 1 + self.left.slash_count() + self.right.slash_count()

    def __iter__(self):
        '''Iterates over the result, then the argument of this category.'''
        yield self.left
        yield self.right
        
    def slashes(self):
        '''For each slash of this compound category, yields a tuple of the category containing that slash
and its labelled index.'''
        yield (self, self.label)
        
        for child in (self.left, self.right):
            if child.is_compound():
                for (node, slash_index) in child.slashes(): 
                    yield (node, slash_index)
                        
    def nested_compound_categories(self):
        return ([self] + 
                 self.left.nested_compound_categories() + 
                 self.right.nested_compound_categories())    

    def is_leaf(self): return False
    def label_text(self): return re.escape(self.slash)

    def is_compound(self): return not self.is_leaf()
    
    def __or__(self, right):
        '''Constructs the complex category (self \ right).'''
        return ComplexCategory(self, BACKWARD, right)
        
    def __div__(self, right):
        '''Constructs the complex category (self / right).'''
        return ComplexCategory(self, FORWARD, right)
