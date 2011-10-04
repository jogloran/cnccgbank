from munge.proc.filter import Filter
from munge.util.dict_utils import CountDict
from munge.trees.traverse import leaves

class SanityChecks(Filter):
    def __init__(self):
        self.nderivs = 0
        self.nwords = 0
        
        self.ecs = 0
        
    def is_trace(self, leaf):
        return leaf.tag == '-NONE-'
        
    def accept_derivation(self, bundle):
        self.nderivs += 1
        self.nwords += len(bundle.derivation.text())
        self.ecs += len([ leaf for leaf in leaves(bundle.derivation) if self.is_trace(leaf) ])
        
    def output(self):
        print "nderivs: %d, nwords: %d, ecs: %d" % (self.nderivs, self.nwords, self.ecs)
        
class PUTokens(Filter):
    def __init__(self):
        Filter.__init__(self)
        
        self.puncts = set()
        
    def accept_leaf(self, leaf):
        if leaf.tag == "PU": self.puncts.add(leaf.lex)
        
    def output(self):
        for punct in sorted(self.puncts):
            print punct