import munge.penn.nodes as N
import re

class Node(N.Node):
    def __init__(self, category, tag, kids, parent=None):
        N.Node.__init__(self, tag, kids, parent)
        self.category = category
        
    def __repr__(self, first=True, suppress_lex=False):
        return "%s(%s {%s} %s)%s" % ("(" if first else "",                      
                                self.tag,
                                self.category, 
                                ' '.join(kid.__repr__(False, suppress_lex) for kid in self.kids), 
                                ")" if first else "")
                                
    def label_text(self):
        return re.escape(repr(self.category))
        
    def ccgbank_repr(self):
        bits = ["(<T %s _ %d>" % (self.category, len(self.kids))]
        
        for kid in self.kids:
            bits.append(kid.ccgbank_repr())
        
        bits.append(")")
        
        return ' '.join(bits)
        
class Leaf(N.Leaf):
    def __init__(self, category, tag, lex, parent=None):
        N.Leaf.__init__(self, tag, lex, parent)
        self.category = category
        
    def __repr__(self, first=True, suppress_lex=False):
        return ("%s(%s {%s} %s)%s" %
            ("(" if first else '',
            self.tag, self.category, '' if suppress_lex else self.lex,
            ")" if first else ''))
            
    def label_text(self):
        return "%s '%s'" % (re.escape(repr(self.category)), self.lex)
        
    @staticmethod
    def detag(tag):
        colon_index = tag.find(':')
        if colon_index != -1:
            return tag[:colon_index]
        else:
            return tag
        
    def ccgbank_repr(self):
        return "(<L %(cat)s %(tag)s %(tag)s %(lex)s %(cat)s>)" % {
            'cat': self.category,
            'tag': self.detag(self.tag),
            'lex': self.lex
        }