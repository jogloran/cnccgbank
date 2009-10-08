from munge.proc.filter import Filter
from munge.util.dict_utils import CountDict

class SanityChecks(Filter):
    def __init__(self):
        self.nderivs = 0
        self.nwords = 0
        
    def accept_derivation(self, bundle):
        self.nderivs += 1
        self.nwords += len(bundle.derivation.text())
        
    def output(self):
        print "nderivs: %d, nwords: %d" % (self.nderivs, self.nwords)
        
class PUTokens(Filter):
    def __init__(self):
        Filter.__init__(self)
        
        self.puncts = set()
        
    def accept_leaf(self, leaf):
        if leaf.tag == "PU": self.puncts.add(leaf.lex)
        
    def output(self):
        for punct in sorted(self.puncts):
            print punct