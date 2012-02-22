# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.ccg.io import WritableCCGbankReader
from munge.io.guess_ccgbank import CCGbankGuesser

import munge.penn.nodes as penn
import munge.ccg.nodes as ccg

LEFT, RIGHT = range(2)
def _insert(old_subtree, new_node, new_cat=None, branching=LEFT):
    print "I am inserting under here: %s" % old_subtree
    was_root = old_subtree.parent is None

    old_parent = old_subtree.parent
    was_left_child = old_parent.lch == old_subtree # XXX: need to do deep equality here (see surgery.py shrink())
        
    if new_cat is None:
        new_cat = new_node.cat.clone() # treat as absorption if new_cat is missing
                
    if branching == LEFT:
        node_to_insert = ccg.Node(new_cat, 0, 2, None,
                            lch=old_subtree,
                            rch=new_node)
    elif branching == RIGHT:
        node_to_insert = ccg.Node(new_cat, 0, 2, None,
                            lch=new_node,
                            rch=old_subtree)
                            
    print "I am inserting this node: %s" % node_to_insert

    if was_root:
        return node_to_insert
    else:    
        if was_left_child:
            old_parent.lch = node_to_insert
        else:
            old_parent.rch = node_to_insert

        return None
        
def node_append(old_subtree, value, new_cat=None):
    return _insert(old_subtree, value, new_cat, branching=LEFT)
        
def node_prepend(old_subtree, value, new_cat=None):
    return _insert(old_subtree, value, new_cat, branching=RIGHT)

class ProxyWritableCCGbankReader(WritableCCGbankReader):
    def __init__(self, filename):
        WritableCCGbankReader.__init__(self, filename)
        
        for deriv in self.derivs:
            deriv.derivation = CCGbankNodeProxy(deriv.derivation)
                    
class ProxyWritableCCGbankGuesser(CCGbankGuesser):
    @staticmethod
    def reader_class(): return ProxyWritableCCGbankReader
        
class CCGbankNodeProxy(object):
    def __init__(self, node):
        self.node = node
        
    class ChildListWrapper(object):
        def __init__(self, node):
            self.node = node
            
        def __getitem__(self, index):
            if index == 0:
                return CCGbankNodeProxy(self.node.lch) if not self.node.lch.is_leaf() else self.node.lch
            elif index == 1:
                return CCGbankNodeProxy(self.node.rch) if not self.node.rch.is_leaf() else self.node.rch
            else:
                raise RuntimeException("Invalid child index %s." % index)
            
        def __len__(self):
            return 2
    
    def __str__(self):
        return str(self.node)
        
    def get_parent(self):
        return CCGbankNodeProxy(self.node.parent)
    def set_parent(self, value):
        self.node.parent = value
    parent = property(get_parent, set_parent)
    
    def get_lch(self):
        return CCGbankNodeProxy(self.node.lch)
    def set_lch(self, v):
        self.node.lch = v
    lch = property(get_lch, set_lch)
        
    def get_rch(self):
        return CCGbankNodeProxy(self.node.rch)
    def set_rch(self, v):
        self.node.rch = v
    rch = property(get_rch, set_rch)
    
    def is_leaf(self):
        return self.node.is_leaf()
        
    def get_cat(self):
        return self.node.cat
    def set_cat(self, cat):
        self.node.cat = cat
    cat = property(get_cat, set_cat)
    
    @property
    def pos1(self): return self.node.pos1
    @property
    def pos2(self): return self.node.pos2
    @property
    def lex(self): return self.node.lex
    @property
    def catfix(self): return self.node.catfix
    @property
    def head_index(self): return self.node.head_index
    @property
    def child_count(self): return self.node.child_count
                
    @property
    def kids(self):
        return CCGbankNodeProxy.ChildListWrapper(self.node)
        
    def __eq__(self, other):
        return other == self.node
        
    def __iter__(self):
        return self.node.__iter__()
        
    def text(self):
        return self.node.text()
