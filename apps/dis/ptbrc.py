from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, find_first

def extract_index(node):
    label = node.tag
    return label[label.rfind('-'):]

class CountPTBRelatives(Filter):
    def __init__(self):
        Filter.__init__(self)
        
        self.rcderivs = 0
        self.total = 0
        
    def accept_derivation(self, bundle):
        root = bundle.derivation
        for node, ctx in tgrep(root, r'{ /SBAR/=SBAR < /WHNP/=WHNP } $ /NP/=NP', with_context=True):
            trace_finder = r"/NP/ & ^/\*T\*-%s/" % extract_index(ctx.whnp)
            if find_first(ctx.sbar, trace_finder) is not None:
                self.rcderivs += 1
                break
        
        self.total += 1
        
    def output(self):
        print 'derivs with rcs: %d/%d=%.2f%%' % (self.rcderivs, self.total, self.rcderivs/float(self.total)*100.)