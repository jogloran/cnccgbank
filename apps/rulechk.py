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
    def __init__(self, indices):
        Filter.__init__(self)
        self.indices = set(map(int, indices.split(',')))
        
    def accept_derivation(self, bundle):
        print bundle.label(),

        error_found = False
        for i, leaf in enumerate(leaves(bundle.derivation)):
            if i in self.indices:
                # check rules starting from this leaf
                for comb, (l, r, p) in combinators_and_path_from_node(leaf):
                    if comb is None:
                        error_found = True
                        print i, rule_repr(l, r, p),

        if not error_found: print 'none',
                    
    arg_names = 'INDICES'
