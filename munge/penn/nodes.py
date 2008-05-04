import re
from munge.trees.traverse import text_without_traces

class Node(object):
    '''Representation of a PTB internal node.'''
    def __init__(self, tag, kids):
        self.tag = tag
        self.kids = kids

    def __repr__(self, first=True):
        return "%s(%s %s)%s" % ("(" if first else "", 
                            self.tag, 
                            ' '.join(kid.__repr__(False) for kid in self.kids), 
                            ")" if first else "")

    def __iter__(self):
        for kid in self.kids: yield kid

    def count(self):
        return len(self.kids)

    def is_leaf(self): return False
    def label_text(self): return re.escape(self.tag)
    
    def text(self):
        return text_without_traces(self)

class Leaf(object):
    '''Representation of a PTB leaf.'''
    def __init__(self, tag, lex):
        self.tag = tag
        self.lex = lex

    def __repr__(self, first=True):
        return "%s(%s %s)%s" % ("(" if first else "", 
                                self.tag, self.lex, 
                                ")" if first else "")

    def __iter__(self): raise StopIteration

    def is_leaf(self): return True
    def label_text(self): return "%s '%s'" % (self.tag, self.lex)
    
    def text(self):
        return text_without_traces(self)
