from munge.proc.filter import Filter
from munge.trees.traverse import nodes
from munge.trees.synttree import pprint_synttree

class AsSynttree(Filter):
    def __init__(self):
        Filter.__init__(self)
        
    def accept_derivation(self, bundle):
        print "\\Tree " + pprint_synttree(bundle.derivation)