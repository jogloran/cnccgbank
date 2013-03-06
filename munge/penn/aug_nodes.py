# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import munge.penn.nodes as N
import re
import munge.cats.nodes as C
from apps.cn.fix_utils import base_tag

class Node(N.Node):
    __slots__ = ["category", "head_index"]
    
    def __init__(self, tag, kids, category=None, parent=None, head_index=None):
        N.Node.__init__(self, tag, kids, parent)
        self.category = category
        self.head_index = head_index
        
    def __repr__(self, first=True, suppress_lex=False, suppress_head_index=False):
        cat_string = "{%s} " % self.category if self.category else ''
        head_index_string = '' if (suppress_head_index or self.head_index is None) else '<%d> ' % self.head_index
        return "%s(%s %s%s%s)%s" % ("(" if first else "",
                                self.tag,
                                head_index_string,
                                cat_string, 
                                ' '.join(kid.__repr__(False, suppress_lex, suppress_head_index) for kid in self.kids), 
                                ")" if first else "")
                                
    def label_text(self):
        if self.category:
            return re.escape(repr(self.category))
        else:
            return re.escape(self.tag)
        
    def ccgbank_repr(self):
        bits = ["(<T %s %s %d>" % (self.category, (self.head_index is not None) and str(self.head_index) or '_', len(self.kids))]
        
        for kid in self.kids:
            bits.append(kid.ccgbank_repr())
        
        bits.append(")")
        
        return ' '.join(bits)
        
class Leaf(N.Leaf):
    __slots__ = ["category"]
    
    def __init__(self, tag, lex, category=None, parent=None):
        N.Leaf.__init__(self, tag, lex, parent)
        self.category = category
        
    def __repr__(self, first=True, suppress_lex=False, suppress_head_index=False):
        cat_string = "{%s} " % self.category if self.category else ''
        return ("%s(%s %s%s)%s" %
            ("(" if first else '',
            self.tag, cat_string, '' if suppress_lex else self.lex,
            ")" if first else ''))
            
    def label_text(self):
        if self.category:
            return "%s '%s'" % (re.escape(repr(self.category)), self.lex)
        else:
            return "%s '%s'" % (re.escape(self.tag), self.lex)
        
    @staticmethod
    def detag(tag):
        colon_index = tag.find(':')
        if colon_index != -1:
            return tag[:colon_index]
        else:
            return tag
        
    def ccgbank_repr(self):
        return "(<L %(cat)s %(basetag)s %(basetag)s %(lex)s %(cat)s>)" % {
            'cat': self.category,
            'basetag': base_tag(self.tag),
            'tag': self.detag(self.tag),
            'lex': self.lex
        }