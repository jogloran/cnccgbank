from munge.proc.trace import Filter
from munge.trees.traverse import leaves

class JustTokens(Filter):
    def __init__(self, outfile):
        self.outfile = outfile
        self.f = file(self.outfile, 'w')
    
    def accept_derivation(self, deriv):
        print >>self.f, "%s|%s" % (deriv.label(), ' '.join(text(deriv.derivation)))