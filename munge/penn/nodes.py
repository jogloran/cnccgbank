class Node:
    def __init__(self, tag, kids):
        self.tag = tag
        self.kids = kids

    def __repr__(self):
        return "<%s %s>" % (self.tag, ' '.join(repr(kid) for kid in self.kids))

    def __iter__(self):
        for kid in self.kids: yield kid

class Leaf:
    def __init__(self, tag, lex):
        self.tag = tag
        self.lex = lex

    def __repr__(self):
        return "<%s %s>" % (self.tag, self.lex)

    def __iter__(self): yield self
