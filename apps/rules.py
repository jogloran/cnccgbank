from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import FixedTgrep, find_all, find_first
from munge.cats.trace import analyse
from munge.util.dict_utils import CountDict, sorted_by_value_desc

class DumpRules(FixedTgrep('''* <1 * <2 *''')):
    def __init__(self):
        DumpRules.__bases__[0].__init__(self)
        self.rules = CountDict()
        
    def match_generator(self, deriv, expr):
        return find_all(deriv, expr)
        
    def match_callback(self, match_node, bundle):
        key = (str(match_node.cat), str(match_node.lch.cat), str(match_node.rch.cat))
        self.rules[key] += 1
        
    def output(self):
        for (p, l, r), f in sorted_by_value_desc(self.rules):
            print p, l, r, f
        

