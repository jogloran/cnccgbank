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
        