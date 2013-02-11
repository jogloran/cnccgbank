# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from collections import defaultdict
from munge.trees.traverse import nodes
from munge.proc.filter import Filter
from itertools import ifilter

def summarise_reductions(reductions, unary=False):
    def reduction_type(head_index):
        if head_index == 0: return 'LEFT'
        if head_index == 1: return 'RIGHT'
        
    return '[ %s ]' % (
        ' , '.join(
            'REDUCE %(arity)s%(redtype)s %(p)s' % dict(
                arity=('UNARY' if unary else 'BINARY'),
                redtype=('' if unary else ' ' + reduction_type(head_index)),
                p=P
            ) for (head_index, P) in reductions
        )
    )
class YZRuleFileMaker(Filter):
    def __init__(self, unary_fn, binary_fn):
        super(YZRuleFileMaker, self).__init__()
        
        self.unary = defaultdict(set)
        self.binary = defaultdict(set)
        
        self.unary_out = file(unary_fn, 'w')
        self.binary_out = file(binary_fn, 'w')
        
    # @staticmethod
    # def signature(node):
        # return "%s , %s:\t:\t[ s ]" 

    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue
            
            if node.count() == 1:
                t = int(node.head_index), str(node.cat)
                self.unary[ str(node[0].cat) ].add(t)
            else:
                t = int(node.head_index), str(node.cat)
                self.binary[ (str(node[0].cat), str(node[1].cat)) ].add(t)
        
    def output(self):
        UnaryTemplate = '%(l)s\t:\t%(reductions)s'
        BinaryTemplate = '%(l)s , %(r)s\t:\t%(reductions)s'
        
        for L, reductions in self.unary.iteritems():
            print >>self.unary_out, UnaryTemplate % dict(l=L, 
                reductions=summarise_reductions(reductions, unary=True))
        for (L, R), reductions in self.binary.iteritems():
            print >>self.binary_out, BinaryTemplate % dict(l=L, r=R, 
                reductions=summarise_reductions(reductions))
            
