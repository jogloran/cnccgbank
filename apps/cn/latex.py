# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from munge.trees.traverse import nodes
from munge.trees.synttree import pprint_synttree

class AsSynttree(Filter):
    def __init__(self):
        Filter.__init__(self)
        
    def accept_derivation(self, bundle):
        print "\\Tree " + pprint_synttree(bundle.derivation)