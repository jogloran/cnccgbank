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
        if isinstance(pattern, dict):
            multi_tgrep(bundle.derivation, pattern)
        elif isinstance(pattern, basestring):
            for match_node in tgrep(bundle.derivation, pattern):
                self.fix(match_node)
        elif isinstance(pattern, function):
            try:
                iterator = iter(pattern(bundle.derivation))
                for match_node in iterator:
                    self.fix(match_node)
            except TypeError:
                raise TypeError('Functions passed as patterns must return an iterable.')
            
        else:
            raise TypeError('Pattern must be a { pattern: callback } dictionary or a pattern string.')
            
        self.write_derivation(bundle)