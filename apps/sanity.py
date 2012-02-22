# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from munge.util.dict_utils import CountDict
from munge.trees.traverse import leaves

def depth(root):
    if root.is_leaf(): return 0
    else:
        return 1 + max(depth(kid) for kid in root)

class AvgDepth(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.depth = 0
        self.nderivs = 0

    def accept_derivation(self, bundle):
        self.depth += depth(bundle.derivation)
        self.nderivs += 1

    def output(self):
        print 'avg depth = %d/%d=%.2f' % (self.depth, self.nderivs, self.depth/float(self.nderivs))

class SanityChecks(Filter):
    def __init__(self):
        self.nderivs = 0
        self.nwords = 0
        
        self.ecs = 0
        self.depth = 0

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