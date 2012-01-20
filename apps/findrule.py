from munge.proc.trace import Filter
from munge.trees.traverse import leaves
from munge.cats.cat_defs import C
class Tgrep(Filter):
    '''Lists occurrences of a context (the category of a focus node, its sibling and its parent).'''
    def __init__(self, focus, sib, parent):
        Filter.__init__(self)
        self.focus = C(focus)
        self.sib = C(sib)
        self.parent = C(parent)
        
        self.sib_as_left = set()
        self.sib_as_right = set()

    def accept_leaf(self, leaf):
        bundle = self.context

        if leaf.cat == self.focus:
            if leaf.parent is None:
                return
                
            was_left_child = leaf.parent.lch is leaf
            if was_left_child:
                if leaf.parent.rch is None: return

                if leaf.parent.rch.cat == self.sib and leaf.parent.cat == self.parent:                           
                    self.sib_as_right.add(bundle.spec_tuple())
            else:
                if leaf.parent.lch.cat == self.sib and leaf.parent.cat == self.parent:
                    self.sib_as_left.add(bundle.spec_tuple())

    def output(self):
        print "(%s %s -> %s)" % (self.sib, self.focus, self.parent)
        print ", ".join("%d:%d(%d)" % t for t in sorted(self.sib_as_left))
        print "(%s %s -> %s)" % (self.focus, self.sib, self.parent)
        print ", ".join("%d:%d(%d)" % t for t in sorted(self.sib_as_right))

    long_opt = "tgrep"
    arg_names = "FOCUS,SIB,PARENT"
