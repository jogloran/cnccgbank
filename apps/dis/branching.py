# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from apps.cn.tag import is_coordination
from munge.trees.traverse import nodes
from munge.trees.pprint import pprint

class BranchingFactor(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.branches = 0
        self.internals = 0
        
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue

            self.branches += node.count()
            self.internals += 1
            
    def output(self):
        print "%d/%d = %.2f" % (self.branches, self.internals, self.branches/float(self.internals))