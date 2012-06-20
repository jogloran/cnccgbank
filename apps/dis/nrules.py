# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

# Number of rules in corpus

from apps.cn.fix_utils import base_tag
from apps.util.tabulation import Tabulation
from munge.trees.traverse import nodes
from munge.proc.filter import Filter
from itertools import ifilter

class NRules(Tabulation(['freqs', 'unary']), Filter):
    def __init__(self):
        super(NRules, self).__init__()
        
    @staticmethod
    def signature(node):
        return ' '.join([base_tag(node.tag)] + [base_tag(kid.tag) for kid in node])
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue
            if node.count() == 1 and node[0].is_leaf():
                self.unary[ self.signature(node) ] += 1
            
            self.freqs[ self.signature(node) ] += 1
        
    def output(self):
        ncats = len(self.freqs)
        ncatsge10 = len(list(ifilter(lambda (k,v): v>=10, self.freqs.iteritems())))
        print "#rules     : %d" % ncats
        print "#rules >=10: %d" % ncatsge10
        print
        
        ncats_nounary = len(list(ifilter(lambda (k,v): k not in self.unary, self.freqs.iteritems())))
        ncatsge10_nounary = len(list(ifilter(lambda (k,v): v>= 10 and k not in self.unary, self.freqs.iteritems())))
        print "#rules (without unary)     : %d" % ncats_nounary
        print "#rules (without unary) >=10: %d" % ncatsge10_nounary
        print
        
        self.do_output()

class IncrementalNRules(NRules):
    def __init__(self):
        super(IncrementalNRules, self).__init__()

        self.ntokens = 0
        self.data_points = [ (0, 0) ]

    def accept_derivation(self, bundle):
        super(IncrementalNRules, self).accept_derivation(bundle)

        self.ntokens += len(bundle.derivation.text())
        self.data_points.append( (self.ntokens, len(self.freqs)) )

    def output(self):
        print '\n'.join( ' '.join(map(str, xy)) for xy in self.data_points )

