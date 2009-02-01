from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, multi_tgrep
from apps.cn.output import OutputDerivation

class Fix(Filter, OutputDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputDerivation.__init__(self)
        
        self.outdir = outdir
        
    def pattern(self):
        raise NotImplementedError('You must subclass FixExtraction to specify a pattern.')
        
    def fix(self, node):
        pass
        
    def accept_derivation(self, bundle):
        pattern = self.pattern()
        if getattr(pattern, "__getitem__"):            
            multi_tgrep(bundle.derivation, pattern)
        else:
            for match_node in tgrep(bundle.derivation, pattern):
                self.fix(node)
        
        self.write_derivation(bundle)