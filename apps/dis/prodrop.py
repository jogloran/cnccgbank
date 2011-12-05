# Find the most common verbs for which pro-drop applies

from munge.proc.filter import Filter
from collections import defaultdict
from munge.proc.tgrep.tgrep import tgrep, find_first, find_all

def find_head(node):
    cur = node
    while not cur.is_leaf():
        cur = cur[ cur.head_index ]
    return cur

class ProdropCheck(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.verbs = defaultdict(int)
        
    def accept_derivation(self, bundle):
        top = bundle.derivation
        for node, ctx in find_all(top, r'* $ { * < ^/\*pro\*/ }', with_context=True):
            head = find_head(node)
            self.verbs[' '.join(head.text())] += 1
            
    def output(self):
        for k, freq in sorted(self.verbs.iteritems(), key=lambda e: e[1], reverse=True):
            print '% 3d | %s' % (freq, k)