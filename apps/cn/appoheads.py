from munge.proc.filter import Filter
from munge.trees.traverse import nodes
from munge.util.dict_utils import sorted_by_value_desc

from collections import defaultdict

class AppositionHeads(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.headfreqs = defaultdict(int)
        
    def get_head(self, node):
        while not node.is_leaf():
            node = node[ node.head_index ]
        return node.lex
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if node.tag.startswith('IP-APP'):
                sibling = node.parent[1]
                head = self.get_head(sibling)
                
                self.headfreqs[head] += 1
                
    def output(self):
        for head, freq in sorted_by_value_desc(self.headfreqs):
            print '% 4d | %s' % (freq, head)