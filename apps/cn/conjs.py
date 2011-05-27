from munge.proc.filter import Filter
from munge.cats.trace import analyse
from munge.util.dict_utils import CountDict, sorted_by_value_desc
from munge.trees.traverse import nodes
from munge.util.err_utils import *
from collections import defaultdict

from apps.cn.tag import is_coordination
from apps.identify_lrhca import base_tag

from collections import defaultdict

def where(pred, seq):
    for e in seq:
        if pred(e): yield e

class ConjAnalysis(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.conjs = defaultdict(set)
        
    def accept_derivation(self, bundle):        
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue
            if is_coordination(node):
                ccs = list(where(lambda kid: kid.tag == 'CC', node.kids))
                for cc in ccs:
                    self.conjs[base_tag(node.tag)].add(cc.lex)
    
    def output(self):
        for top_tag, ccs in sorted(self.conjs.iteritems()):
            print '% 5s | %s' % (top_tag, ' '.join(sorted(ccs)))
            
            
