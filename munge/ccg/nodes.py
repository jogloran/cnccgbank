class Node:
    '''Representation of a CCGbank internal node.'''
    def __init__(self, cat, ind1, ind2, parent, lch=None, rch=None):
        self.cat = cat
        self.ind1, self.ind2 = ind1, ind2
        self.parent = parent

        self.lch, self.rch = lch, rch

    def __repr__(self):
        return "(<T %s %s %s> %s %s)" % \
                (self.cat, self.ind1, self.ind2, \
                 self.lch, self.rch or '')

    def get_lch(self): return self.lch
    def set_lch(self, new_lch):
        self.lch = new_lch
        self.lch.parent = self
    lch = property(get_lch, set_lch)

    def get_rch(self): return self.rch
    def set_rch(self, new_rch):
        self.rch = new_rch
        self.rch.parent = self
    rch = property(get_rch, set_rch)

class Leaf:
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
