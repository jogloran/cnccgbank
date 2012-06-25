from munge.proc.filter import Filter
from munge.trees.traverse import leaves
from munge.cats.paths import applications, category_path_to_root
from munge.util.iter_utils import each_pair
from munge.cats.trace import analyse
from munge.util.deco_utils import cast_to

def combinators_and_path_from_node(node):
    path = category_path_to_root(node)
    for (prev_l, prev_r, _), (l, r, was_flipped) in each_pair(path):
        l, r, p = prev_l, prev_r, r if was_flipped else l
        yield analyse(l, r, p), (l, r, p)
    
def rule_repr(l, r, p):
    if r is None:
        return '%s -> %s' % (l, p)
    else:
        return '%s %s -> %s' % (l, r, p)

class CheckRules(Filter):
    def __init__(self, index):
        Filter.__init__(self)
        self.index = int(index)
        
    def accept_derivation(self, bundle):
        for i, leaf in enumerate(leaves(bundle.derivation)):
            if i == self.index:
                # check rules starting from this leaf
                for comb, (l, r, p) in combinators_and_path_from_node(leaf):
                    if comb is None:
                        print rule_repr(l, r, p)
                    
    arg_names = 'INDEX'