import re
from collections import defaultdict

from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, find_first
from munge.util.tgrep_utils import get_first
from munge.util.func_utils import const
from munge.util.dict_utils import sorted_by_value_desc

def extract_index(node):
    label = node.tag
    return label[label.rfind('-'):]

class CountPTBRelatives(Filter):
    def __init__(self):
        Filter.__init__(self)
        
        self.rcderivs = 0
        self.total = 0
        self.parents = defaultdict(int)
        
    def accept_derivation(self, bundle):
        found_rc = False
        root = bundle.derivation
        for node, ctx in tgrep(root, r'{ /SBAR/=SBAR < /WHNP/=WHNP } $ /NP/=NP', with_context=True):
            trace_finder = r"^/\*T\*%s/" % extract_index(ctx.whnp)
            trace_node = get_first(ctx.sbar, trace_finder)
            if trace_node is not None:
                if not found_rc:
                    self.rcderivs += 1
                    found_rc = True

                parent_type = trace_node.parent.tag
                parent_type = re.sub(r'-\d+$', '', parent_type)
                self.parents[ parent_type ] += 1
        
        self.total += 1
        
    def output(self):
        print 'trace types:'
        for k, v in sorted_by_value_desc(self.parents):
            print '% 5d | %s' % (v, k)
        print 'derivs with rcs: %d/%d=%.2f%%' % (self.rcderivs, self.total, self.rcderivs/float(self.total)*100.)
        
class CountPCTBRelatives(Filter):
    def __init__(self):
        Filter.__init__(self)
        
        self.rcderivs = 0
        self.total = 0
        self.parents = defaultdict(int)
        
    def accept_derivation(self, bundle):
        found_rc = False
        root = bundle.derivation
        for node, ctx in tgrep(root, r'/CP/ < { /CP/=CP < /DEC/ } < /WHNP/=WHNP', with_context=True):
            trace_finder = r"^/\*T\*%s/" % extract_index(ctx.whnp)
            trace_node = get_first(ctx.cp, trace_finder)

            if trace_node:
                if not found_rc:
                    self.rcderivs += 1
                    found_rc = True

                self.parents[ trace_node.parent.tag ] += 1
        
        self.total += 1
        
    def output(self):
        print 'trace types:'
        for k, v in sorted_by_value_desc(self.parents):
            print '% 5d | %s' % (v, k)
        print 'derivs with rcs: %d/%d=%.2f%%' % (self.rcderivs, self.total, self.rcderivs/float(self.total)*100.)
