# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from munge.cats.trace import analyse
from munge.trees.traverse import nodes

class DerivCount(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.nderivs = 0
        
    def accept_derivation(self, bundle):
        self.nderivs += 1
        
    def output(self):
        print self.nderivs

class PunctuationCount(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.n = 0
        self.total = 0

    puncts = (",",)
    def accept_derivation(self, bundle):
        self.total += 1
        
        toks = bundle.derivation.text()
        for tok in toks:
            if tok in self.puncts:
                self.n += 1
                break
            
    def output(self):
        print "(%d/%d) = %d" % (self.n, self.total, self.n/float(self.total)*100.0)

class AnalysisCount(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.total = 0
        self.l, self.r = 0, 0
        self.other = 0
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue
            
            self.total += 1
            
            result = analyse(node.lch.cat, node.rch and node.rch.cat, node.cat)
            if result == 'l_punct_absorb':
                self.l += 1
            elif result == 'r_punct_absorb':
                self.r += 1
            else:
                self.other += 1
                
    def output(self):
        print "l: %s, r: %s, other: %s" % (self.l, self.r, self.other)
        print "total: %s" % self.total