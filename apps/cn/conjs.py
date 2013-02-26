# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from munge.trees.traverse import nodes
from munge.util.err_utils import *
from collections import defaultdict

from apps.cn.tag import is_coordination
from apps.cn.fix_utils import base_tag

from collections import defaultdict

def where(pred, seq):
    for e in seq:
        if pred(e): yield e

class ConjAnalysis(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.conjs = defaultdict(lambda: defaultdict(int))
        self.inverse = defaultdict(lambda: defaultdict(int))
        
    def accept_derivation(self, bundle):        
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue
            if is_coordination(node):
                ccs = list(where(lambda kid: kid.tag == 'CC', node.kids))
                for cc in ccs:
                    self.conjs[base_tag(node.tag)][cc.lex] += 1
                    self.inverse[cc.lex][base_tag(node.tag)] += 1
    
    def output(self):
        for top_tag, ccs in sorted(self.conjs.iteritems()):
            sorted_by_freq = sorted(ccs.iteritems(), key=lambda e: e[1], reverse=True)
            print '% 5s | %s' % (top_tag, '; '.join('%s (%s)' % (lex, freq) for (lex, freq) in sorted_by_freq))
            # print '% 5s' % top_tag,
            # first = True
            # for k, v in sorted(ccs.iteritems(), key=lambda e: e[1], reverse=True):
            #     if not first:
            #         print '     ',
            #     else:
            #         first = False
            #     print '| % 5d %s' % (v, k)
            
        print
        for top_tag, ccs in sorted(self.inverse.iteritems(), key=lambda (k, v): sum(v.values()), reverse=True):
            sorted_by_freq = sorted(ccs.iteritems(), key=lambda e: e[1], reverse=True)
            print '% 5s | %s' % (top_tag, '; '.join('%s (%s)' % (lex, freq) for (lex, freq) in sorted_by_freq))
        
