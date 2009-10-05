from munge.proc.filter import Filter
from munge.cats.trace import analyse
from munge.util.dict_utils import CountDict, sorted_by_value_desc
from munge.trees.traverse import nodes
from munge.util.err_utils import *
from munge.cats.trace import analyse

class CountRules(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.counts = CountDict()
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue
                    
            l, p = node[0].cat, node.cat
            r = node[1].cat if node.count() > 1 else None
            
            self.counts[ tuple(n for n in (l, r, p)) ] += 1
    
    def output(self):
        for (l, r, p), freq in sorted_by_value_desc(self.counts):
            print "%8d | %15s  %-15s -> %-15s [%s]" % (freq, l, r, p, analyse(l, r, p))
            
class ListAtoms(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.atoms = set()
                
    @staticmethod
    def get_atoms(cat):
        result = set()
        for sub in cat:
            if not sub.is_complex():
                # remove any features
                sub = sub.clone()
                sub.features = []
                result.add(sub)
            else: result.update(ListAtoms.get_atoms(sub))
        return result
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            self.atoms.update(ListAtoms.get_atoms(node.cat))
        
    def output(self):
        for atom in sorted(map(str, self.atoms)):
            print atom