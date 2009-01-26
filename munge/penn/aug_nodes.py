import munge.penn.nodes as N
import re

class Node(N.Node):
    def __init__(self, category, tag, kids, parent=None):
        N.Node.__init__(self, tag, kids, parent)
        self.category = category
        
    def __repr__(self, first=True):
        return "%s(%s {%s} %s)%s" % ("(" if first else "",                      
                                self.tag,
                                self.category, 
                                ' '.join(kid.__repr__(False) for kid in self.kids), 
                                ")" if first else "")
                                
    def label_text(self):
        return re.escape(repr(self.category))
        
class Leaf(N.Leaf):
    def __init__(self, category, tag, lex, parent=None):
        N.Leaf.__init__(self, tag, lex, parent)
        self.category = category
        
    def __repr__(self, first=True):
        return ("%s(%s {%s} %s)%s" %
            ("(" if first else '',
            self.tag, self.category, self.lex,
            ")" if first else ''))
            
    def label_text(self):
        return "%s '%s'" % (re.escape(repr(self.category)), self.lex)