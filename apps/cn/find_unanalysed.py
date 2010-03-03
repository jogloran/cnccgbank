import sys
from glob import glob
from munge.ccg.io import CCGbankReader
from munge.cats.trace import analyse
from munge.trees.traverse import nodes
from collections import defaultdict
from munge.util.err_utils import debug
from apps.util.config import config
from munge.util.dict_utils import sorted_by_value_desc

config.show_vars = False

combs = defaultdict(lambda: 0)
unrecognised_rules = defaultdict(lambda: 0)
total, with_unrecognised_rules = 0, 0
for file in glob(sys.argv[1]):
    for bundle in CCGbankReader(file):
        has_unrecognised_rules = False
        
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue
            
            lrp = map(lambda e: e and e.cat, (node[0], node[1] if node.count() > 0 else None, node))
            
            comb = analyse(*lrp)
            if comb:
                combs[comb] += 1
            else:
                #debug("Unrecognised rule %s %s -> %s", *lrp)
                l, r, p = lrp
                unrecognised_rules[ (str(l), str(r), str(p)) ] += 1
                if not has_unrecognised_rules:
                    with_unrecognised_rules += 1
                has_unrecognised_rules = True
                
        total += 1

print "With unrecognised rules: %d/%d=%.2f" % (with_unrecognised_rules, total, with_unrecognised_rules/float(total)*100.0)
for rule, freq in sorted_by_value_desc(unrecognised_rules):
    l, r, p = rule
    print "% 4d | %20s %20s -> %s" % (freq, l, r, p)
