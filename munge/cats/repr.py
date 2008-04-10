from copy import copy
import re

BACKWARD, FORWARD = 1, 2

class AtomicCategory(object):
    def __init__(self, cat, features=None):
        self.cat = cat
        self.features = features or []

    def label(self): return self

    def feature_repr(self):
        return ''.join("[%s]" % feature for feature in self.features)

    def __repr__(self, first=True):
        '''A (non-evaluable) representation of this category. Ignores its first argument
        so it can be treated uniformly with CompoundCategory.'''
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

    def labelled(index=0): return index

    def slash_count(self): return 0

    def is_leaf(self): return True
    def label_text(self): return re.escape(self.cat)

class CompoundCategory(object):
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
        return "%(open)s%(lch)s%(slash)s%(rch)s%(close)s%(feats)s" % {
                'open': "" if first else "(",
                'lch': self.left.make_repr(False),
                'slash': self.slash,
                'rch': self.right.make_repr(False),
                'close': "" if first else ")",
                'feats': self.feature_repr()
                }

    def clone(self): return CompoundCategory(self.left.clone(), self.direction, self.right and self.right.clone(), self.mode, copy(self.features))

    def __eq__(self, other):
        if not isinstance(other, CompoundCategory): return false

        return self.equal_ignoring_features(other) or self.features == other.features

    def equal_ignoring_features(self, other):
        if not isinstance(other, CompoundCategory): return false

        return self.direction == other.direction and \
                self.left == other.left and \
                self.right == other.right

    def labelled(index=0):
        self.label = index
        index += 1 # the current node gets the label _index_
        index = self.left.labelled(index)
        index = self.right.labelled(index)
        return index

    def slash_count(self):
        return 1 + self.left.slash_count() + self.right.slash_count()

    def __iter__(self):
        yield self.left
        yield self.right

    def is_leaf(self): return False
    def label_text(self): return re.escape(self.slash)
