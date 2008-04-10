import re

class Node(object):
    '''Representation of a CCGbank internal node.'''
    def __init__(self, cat, ind1, ind2, parent, lch=None, rch=None):
        self.cat = cat
        self.ind1, self.ind2 = ind1, ind2
        self.parent = parent

        self._lch, self._rch = lch, rch

    def __repr__(self):
        return "(<T %s %s %s> %s %s)" % \
                (self.cat, self.ind1, self.ind2, \
                 self.lch, self.rch or '')

    def __iter__(self):
        yield self.lch
        if self.rch: yield self.rch

    def get_lch(self): return self._lch
    def set_lch(self, new_lch):
        if not new_lch: return
        self._lch = new_lch
        self._lch.parent = self
    lch = property(get_lch, set_lch)

    def get_rch(self): return self._rch
    def set_rch(self, new_rch):
        if not new_rch: return
        self._rch = new_rch
        self._rch.parent = self
    rch = property(get_rch, set_rch)

    def __eq__(self, other):
        return self.cat == other.cat and \
               self.lch == other.lch and \
               self.rch == other.rch and \
               self.ind1 == other.ind1 and \
               self.ind2 == other.ind2

    def is_leaf(self): return False
    def label_text(self): return re.escape(str(self.cat))

class Leaf(object):
    '''Representation of a CCGbank leaf.'''
    def __init__(self, cat, pos1, pos2, lex, catfix, parent=None):
        self.cat = cat
        self.pos1, self.pos2 = pos1, pos2
        self.lex = lex
        self.catfix = catfix
        self.parent = parent

    def __repr__(self):
        return "(<L %s %s %s %s %s>)" % \
                (self.cat, self.pos1, self.pos2, \
                 self.lex, self.catfix)

    def __eq__(self, other):
        return self.cat == other.cat and \
               self.pos1 == other.pos1 and \
               self.pos2 == other.pos2 and \
               self.lex == other.lex and \
               self.catfix == other.catfix
               
    def is_leaf(self): return True
    def label_text(self): return """%s '%s'""" % (re.escape(str(self.cat)), self.lex)
