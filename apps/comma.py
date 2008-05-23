import sys

from munge.proc.trace import Filter
from munge.util.dict_utils import CountDict, sorted_by_value_desc
from munge.cats.trace import analyse
from munge.cats.cat_defs import C
from munge.util.list_utils import list_preview

class AnalyseCommas(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.envs = CountDict()

    def accept_leaf(self, leaf):
        if leaf.cat == C(','):
            was_left_child = leaf.parent.lch is leaf
            if was_left_child:
                environment = map(lambda e: str(e.cat), [ leaf, leaf.parent.rch, leaf.parent ])
            else:
                environment = map(lambda e: str(e.cat), [ leaf.parent.lch, leaf, leaf.parent ])

            self.envs[ tuple(environment) ] += 1
            
class AnalyseAbsorption(Filter):
    LEFT, RIGHT = 0, 1
    
    def __init__(self):
        Filter.__init__(self)
        self.envs = CountDict()

    def accept_leaf(self, leaf):
        if leaf.cat == C(','):
            if leaf.parent is None or leaf.parent.parent is None: return
            
            was_left_child = leaf.parent.lch is leaf
            if was_left_child:
                environment = [self.LEFT] + map(lambda e: str(e.cat), [ leaf.parent.parent.lch, leaf.parent, leaf.parent.parent ])
            else:
                if leaf.parent.parent.rch is None: return
                
                environment = [self.RIGHT] + map(lambda e: str(e.cat), [ leaf.parent, leaf.parent.parent.rch, leaf.parent.parent ])

            self.envs[ tuple(environment) ] += 1
        
class AnalyseAbsorptionSupertags(Filter):
    LEFT, RIGHT = 0, 1
    
    def __init__(self):
        Filter.__init__(self)
        self.envs = CountDict()

    def accept_leaf(self, leaf):
        if leaf.cat == C(','):
            if leaf.parent is None or leaf.parent.parent is None: return
            
            was_left_child = leaf.parent.lch is leaf
            if was_left_child:
                environment = [self.LEFT] + map(lambda e: str(e.cat), [ self.rightmost(leaf.parent.parent.lch), leaf.parent, leaf.parent.parent ])
            else:
                if leaf.parent.parent.rch is None: return

                environment = [self.RIGHT] + map(lambda e: str(e.cat), [ leaf.parent, self.leftmost(leaf.parent.parent.rch), leaf.parent.parent ])

            self.envs[ tuple(environment) ] += 1
     
    @staticmethod
    def leftmost(node):
        while node.lch is not None:
            node = node.lch
        return node
    @staticmethod
    def rightmost(node):
        while node.rch is not None:
            node = node.rch
        return node
        
class PrintAbsorptionSupertagsCountsByBranching(AnalyseAbsorptionSupertags):
    def __init__(self):
        AnalyseAbsorptionSupertags.__init__(self)
        
    def output(self):
        pass
        # as_left = {}
        # as_right = {}
        # for (side, l, r, p), f in self.envs.iteritems():
        #     if side == AnalyseAbsorptionSupertags.LEFT:
        #         as_left[ (l, r, p) ] = f
        #     elif side == AnalyseAbsorptionSupertags.RIGHT:
        #         as_right[ (l, r, p) ] = f
        # 
        # print "(X ,) Y
        # print "--------"
        # for (l, r, p), f in sorted_by_value_desc(as_left):
        #     print "% 10d [%28s] (%s ,) %s -> %s" % (f, analyse(C(l), C(r), C(p)), l, r, p)
        # 
        # print "X (, Y) -> Z"
        # print "--------"
        # for (l, r, p), f in sorted_by_value_desc(as_right):
        #     print "% 10d [%28s] %s (, %s) -> %s" % (f, analyse(C(l), C(r), C(p)), l, r, p)
                       
class PrintAbsorptionCounts(AnalyseAbsorption):
    def __init__(self):
        AnalyseAbsorption.__init__(self)

    def output(self):
        for (comma_on_left, lch, rch, parent), freq in sorted_by_value_desc(self.envs):
            print "% 10d %s (%s %s -> %s)" % (freq, "L" if comma_on_left else "R", lch, rch, parent)
    

class PrintCommaCounts(AnalyseCommas):
    '''Prints comma occurrence counts by descending frequency.''' 
    def __init__(self):
        AnalyseCommas.__init__(self)

    def output(self):
        for (lch, rch, parent), freq in sorted_by_value_desc(self.envs):
            print "% 10d (%s %s -> %s)" % (freq, lch, rch, parent)

    long_opt = "comma-counts"
    
from collections import defaultdict
class PrintAbsorptionCountsByBranching(AnalyseAbsorption):
    def __init__(self):
        AnalyseAbsorption.__init__(self)

    def output(self):
        as_left = {}
        as_right = {}
        
        for (side, l, r, p), f in self.envs.iteritems():
            if side == AnalyseAbsorption.LEFT:
                as_left[ (l, r, p) ] = f
            elif side == AnalyseAbsorption.RIGHT:
                as_right[ (l, r, p) ] = f

        print "(X ,) Y -> Z"
        print "--------"
        for (l, r, p), f in sorted_by_value_desc(as_left):
            print "% 10d [%28s] (%s ,) %s -> %s" % (f, analyse(C(l), C(r), C(p)), l, r, p)

        print "X (, Y) -> Z"
        print "--------"
        for (l, r, p), f in sorted_by_value_desc(as_right):
            print "% 10d [%28s] %s (, %s) -> %s" % (f, analyse(C(l), C(r), C(p)), l, r, p)
            
class PrintCommaCountsByBranching(AnalyseCommas):
    '''Prints comma occurrence counts by descending frequency together with the rule used.''' 
    def __init__(self):
        AnalyseCommas.__init__(self)

    def output(self):
        as_left = {}
        as_right = {}
        for (l, r, p), f in self.envs.iteritems():
            if str(l) == ',':
                as_left[ (l, r, p) ] = f
            elif str(r) == ',':
                as_right[ (l, r, p) ] = f

        print ", _ -> _"
        print "--------"
        for (l, r, p), f in sorted_by_value_desc(as_left):
            print "% 10d [%28s] %s %20s -> %s" % (f, analyse(C(l), C(r), C(p)), l, r, p)
            
        print "_ , -> _"
        print "--------"
        for (l, r, p), f in sorted_by_value_desc(as_right):
            print "% 10d [%28s] %20s %s -> %s" % (f, analyse(C(l), C(r), C(p)), l, r, p)

    long_opt = "comma-counts-branching"
