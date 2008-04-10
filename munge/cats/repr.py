from copy import copy
from munge.util.exceptions import CatParseException
import re

ShowModes = True

BACKWARD, FORWARD = range(2)
APPLY, ALL, COMP, NULL = range(4)

class AtomicCategory(object):
    def __init__(self, cat, features=None):
        self.cat = cat
        self.features = features or []

    def label(self): return self

    def feature_repr(self):
        return ''.join("[%s]" % feature for feature in self.features)

    def __repr__(self, first=True):
        '''A (non-evaluable) representation of this category. Ignores its first argument
        so it can be treated uniformly with ComplexCategory.'''
        return self.cat + self.feature_repr()

    # AtomicCategory is immutable
    def clone(self): return self

    def has_feature(self, feature): return feature in self.features

    def __eq__(self, other):
        if not isinstance(other, AtomicCategory): return False
        return self.equal_ignoring_features(other) and \
                self.features == other.features

    def equal_ignoring_features(self, other):
        if not isinstance(other, AtomicCategory): return False
        return self.cat == other.cat

    def labelled(self, index=0): return index
    def is_labelled(self): return False

    def slash_count(self): return 0

    def is_leaf(self): return True
    def label_text(self): return re.escape(self.cat)

class ComplexCategory(object):
    # Index i into mode_symbols references the mode with integer representation i.
    mode_symbols = "*.@-"
    def get_mode_symbol(self, mode_index):
        if not mode_index: return ''

        if 0 <= mode_index < len(self.mode_symbols): return self.mode_symbols[mode_index]
        else: raise CatParseException('Mode index %s invalid or out of range.' % mode_index)

    def __init__(self, left, direction, right, mode=None, features=None, label=None):
        self.left, self.direction, self.right = left, direction, right
        self.mode = mode
        self.features = features or []
        self.label = label

        self.slash = "\\" if self.direction == BACKWARD else "/"

    def feature_repr(self):
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
        return ComplexCategory(self.left.clone(),
                               self.direction, 
                               self.right and self.right.clone(),
                               self.mode, copy(self.features))

    def __eq__(self, other):
        if not isinstance(other, ComplexCategory): return False

        return self.equal_ignoring_features(other) or self.features == other.features

    def equal_ignoring_features(self, other):
        if not isinstance(other, ComplexCategory): return False

        return self.direction == other.direction and \
                self.left == other.left and \
                self.right == other.right

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
        yield self.left
        yield self.right

    def is_leaf(self): return False
    def label_text(self): return re.escape(self.slash)