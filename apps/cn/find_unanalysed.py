try:
    import psyco
    psyco.full()
except ImportError:
    pass

import sys
from glob import glob
from munge.ccg.io import CCGbankReader
from munge.cats.trace import analyse
from munge.trees.traverse import nodes
from collections import defaultdict
from munge.util.err_utils import debug
from apps.util.config import config
from munge.util.dict_utils import sorted_by_value_desc
from munge.cats.cat_defs import *

config.show_vars = False

combs = defaultdict(lambda: 0)
unrecognised_rules = defaultdict(lambda: 0)
total, with_unrecognised_rules = 0, 0
ucp_rules = defaultdict(lambda: 0)
with_ucp = 0

unary, binary = defaultdict(lambda: 0), defaultdict(lambda: 0)

def is_ucp(l, r, p):
    if r is None: return False
    
    return l in (conj, C('LCM'), C(',')) and p.has_feature('conj') and p != r

for file in glob(sys.argv[1]):
    for bundle in CCGbankReader(file):
        has_unrecognised_rules, has_ucp = False, False
        
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue
            
            lrp = map(lambda e: e and e.cat, (node[0], node[1] if node.count() > 0 else None, node))
            
            comb = analyse(*lrp)
            l, r, p = lrp
            rule_tuple = (str(l), str(r), str(p))
            
            if comb:
                combs[comb] += 1
            elif is_ucp(*lrp):
                ucp_rules[rule_tuple] += 1
                if not has_ucp:
                    with_ucp += 1
                has_ucp = True
            else:
                # Split unrecognised rules by type
                if r:
                    binary[rule_tuple] += 1
                else:
                    unary[rule_tuple] += 1
                    
                unrecognised_rules[rule_tuple] += 1
                if not has_unrecognised_rules:
                    with_unrecognised_rules += 1
                has_unrecognised_rules = True
                
        total += 1

print "With unrecognised rules: %d/%d=%.2f" % (with_unrecognised_rules, total, with_unrecognised_rules/float(total)*100.0)
for rule, freq in sorted_by_value_desc(unrecognised_rules):
    l, r, p = rule
    print "% 4d | %20s %20s -> %s" % (freq, l, r, p)

print "UCP rules: %d/%d=%.2f" % (with_ucp, total, with_ucp/float(total)*100.0)
for rule, freq in sorted_by_value_desc(ucp_rules):
    l, r, p = rule
    print "% 4d | %20s %20s -> %s" % (freq, l, r, p)
    
print "Unrecognised binary rules:"
for rule, freq in sorted_by_value_desc(binary):
    l, r, p = rule
    print "% 4d | %20s %20s -> %s" % (freq, l, r, p)
    
print "Unrecognised unary rules:"
for rule, freq in sorted_by_value_desc(unary):
    l, r, p = rule
    print "% 4d | %20s %20s -> %s" % (freq, l, r, p)
