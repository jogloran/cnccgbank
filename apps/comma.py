from munge.proc.trace import Filter
from munge.util.dict_utils import CountDict, sorted_by_value_desc
from munge.cats.trace import analyse
from munge.cats.cat_defs import C
import sys

class AnalyseCommas(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.envs = CountDict()

    def accept_leaf(self, leaf):
        if leaf.lex == ',':
            was_left_child = leaf.parent.lch is leaf
            if was_left_child:
                environment = map(lambda e: str(e.cat), [ leaf, leaf.parent.rch, leaf.parent ])
            else:
                environment = map(lambda e: str(e.cat), [ leaf.parent.lch, leaf, leaf.parent ])

            self.envs[ tuple(environment) ] += 1

class PrintCommaCounts(AnalyseCommas):
    '''Prints comma occurrence counts by descending frequency.''' 
    def __init__(self):
        AnalyseCommas.__init__(self)

    def output(self):
        for (lch, rch, parent), freq in sorted_by_value_desc(self.envs):
            print "% 10d (%s %s -> %s)" % (freq, lch, rch, parent)

    long_opt = "comma-counts"

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
