from itertools import izip, count

from munge.proc.tgrep.tgrep import FixedTgrep, find_all, find_first
from munge.util.dict_utils import CountDict, sorted_by_value_desc
from munge.cats.trace import analyse
from munge.cats.cat_defs import C

class PrintCommaCountsByBranching(FixedTgrep(r'{, $ /.+/} > /.+/')):
    '''Prints comma occurrence counts by descending frequency together with the rule used.'''
    def __init__(self):
        PrintCommaCountsByBranching.__bases__[0].__init__(self)
        self.envs = CountDict()
        
    def output(self):
        as_left = {}
        as_right = {}
        for (l, r, p), f in self.envs.iteritems():
            if l == ',':
                as_left[(l, r, p)] = f
            else:
                as_right[(l, r, p)] = f
        
        print ", _ -> _"
        print "--------"
        for (l, r, p), f in sorted_by_value_desc(as_left):
            print "% 10d [%28s] %s %20s -> %s" % (f, analyse(C(l), C(r), C(p)), l, r, p)
        print "_ , -> _"
        print "--------"
        for (l, r, p), f in sorted_by_value_desc(as_right):
            print "% 10d [%28s] %20s %s -> %s" % (f, analyse(C(l), C(r), C(p)), l, r, p)
        
    def match_generator(self, deriv, expr):
        return find_all(deriv, expr)
    
    def match_callback(self, match_node, bundle):
        is_left_child = match_node.parent.lch is match_node
        if is_left_child:
            self.envs[ (str(match_node.cat), str(match_node.parent.rch.cat), str(match_node.parent.cat)) ] += 1
        else:                                                             
            self.envs[ (str(match_node.parent.lch.cat), str(match_node.cat), str(match_node.parent.cat)) ] += 1
            
        
class PrintAbsorptionCountsByBranching2(FixedTgrep(r'''
     /.+/  [ <1 { /.+/ <1 /.+/ <2 , } <2 /.+/ ] | [ <1 { /.+/ <1 , <2 /.+/ } <2 /.+/ ] | [ <2 { /.+/ <1 /.+/ <2 , } <1 /.+/ ] | [ <2 { /.+/ <1 , <2 /.+/ } <1 /.+/ ]
'''
)):
    def __init__(self):
        PrintAbsorptionCountsByBranching2.__bases__[0].__init__(self)
        self.e0 = CountDict()
        self.e1 = CountDict()
        self.e2 = CountDict()
        self.e3 = CountDict()
        
    def output(self):
        headings = ("(%s ,) %s -> %s",
                    "(, %s) %s -> %s",
                    "%s (%s ,) -> %s",
                    "%s (, %s) -> %s")
        for heading, index in izip(headings, count()):
            env_hash = getattr(self, 'e%d' % index)
            print heading % ('X', 'Y', 'Z')
            print "-" * len(heading)
            
            for (l, r, p), f in sorted_by_value_desc(env_hash):
                print ("% 10d [%28s] " + heading) % (f, analyse(C(l), C(r), C(p)), l, r, p)
            
    def match_generator(self, deriv, expr):
        return find_all(deriv, expr)
    
    def match_callback(self, m, bundle):
        # (X ,) Y -> Z 0
        # (, X) Y -> Z 1
        # X (Y ,) -> Z 2
        # X (, Y) -> Z 3
        if not m.lch.is_leaf():
            if m.lch.rch is not None and str(m.lch.rch.cat) == ',':
                self.e0[ (str(m.lch.lch.cat), str(m.rch.cat), str(m.cat)) ] += 1
            elif str(m.lch.lch.cat) == ',':
                self.e1[ (str(m.lch.rch.cat), str(m.rch.cat), str(m.cat)) ] += 1
            
        if not m.rch.is_leaf():
            if m.rch.rch is not None and str(m.rch.rch.cat) == ',':
                self.e2[ (str(m.lch.cat), str(m.rch.lch.cat), str(m.cat)) ] += 1
            elif str(m.rch.lch.cat) == ',':
                self.e3[ (str(m.lch.cat), str(m.rch.rch.cat), str(m.cat)) ] += 1
