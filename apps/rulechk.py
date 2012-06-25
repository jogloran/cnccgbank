from munge.proc.filter import Filter
from munge.trees.traverse import leaves
from munge.cats.paths import applications
from munge.util.deco_utils import cast_to

class CheckRules(Filter):
    def __init__(self, index):
        Filter.__init__(self)
        self.index = int(index)
        
    def accept_derivation(self, bundle):
        for i, leaf in enumerate(leaves(bundle.derivation)):
            if i == self.index:
                # check rules starting from this leaf
                for rule in applications(leaf):
                    print rule
                    
    arg_names = 'INDEX'