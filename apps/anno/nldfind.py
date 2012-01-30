from munge.proc.filter import Filter
from apps.cn.output import *
from munge.util.tgrep_utils import get_first

class NLDFinder(Filter, OutputPrefacedPTBDerivation):
    Patterns = [
    # F = filler
    # T = trace
        (r'/CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < { /CP/ < { /IP/ << { /NP-OBJ/ < "-NONE-" $ /V/=V } } < /DEC/ }', 'objex'),
        (r'/CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < { /CP/ < { /IP/ << { /NP-SBJ/ < "-NONE-" $ /V/=V } } < /DEC/ }', 'subjex'),
        (r'/CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < {          /IP/ << { /NP-OBJ/ < "-NONE-" $ /V/=V } }', 'objex_null'),
        (r'/CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < {          /IP/ << { /NP-SBJ/ < "-NONE-" $ /V/=V } }', 'subjex_null'),
        (r'/IP/ < /-TPC-\d+/a=F << { * < { "-NONE-" & ^/\*T\*-\d+/=T } $ /V/=V }', 'gaptop'),
        (r'/LB/ $ { /IP/ << { "-NONE-" & ^/\*-\d+/ } }', 'lb_gap'),
        (r'/LB/ $ /IP/', 'lb_nongap'),
        (r'/SB/ $ { /IP/ << { "-NONE-" & ^/\*-\d+/ } }', 'sb_gap'),
        (r'/SB/ $ /VP/', 'sb_nongap'),
    ]
    def matches(self, pattern, node):
        match = get_first(node, pattern)
        return match is not None
        
    def accept_derivation(self, bundle):
        root = bundle.derivation
        for (pattern, nldtype) in self.Patterns:
            if self.matches(pattern, root):
                self.write_derivation(bundle, subdir=nldtype)
                
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPrefacedPTBDerivation.__init__(self, outdir)