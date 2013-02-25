# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import re
from munge.proc.filter import Filter
from munge.trees.traverse import nodes
from apps.cn.fix_utils import base_tag

WordTags = frozenset(
    ('AD,BA,CD,CS,DEC,DEG,DER,DEV,DT,ETC,FW,IJ,JJ,LB,LC,M,MSP,NN,NR,NT,OD,P,PN,SB,SP,VA,VC,VE,VV').split(',')
)

class BadRules(Filter):
    def __init__(self, outdir):
        Filter.__init__(self)
        self.nbad = 0
        self.nderivs = 0
        
    def accept_derivation(self, bundle):
        def kids_have_same_tag(node):
            def tags_are_equal(t1, t2):
                if t1[0] == 'V' and t2[0] == 'V': return True
                if t1[0] == 'N' and t2[0] == 'N': return True
                return t1 == t2
            return all(tags_are_equal(node[0].tag, other.tag) for other in node[1:])
        self.nderivs += 1
        for node in nodes(bundle.derivation):
            if (node.count() > 1 and 
                (not node.tag.startswith('NP')) and
                (not node.tag.startswith('ADJP')) and
                (not node.tag.startswith('FRAG')) and
                (not node.tag.startswith('FLR')) and
                (not base_tag(node.tag) in ('VCD', 'VRD', 'VCP', 'VNV', 'VPT', 'VSB')) and
                (not kids_have_same_tag(node)) and
                all(base_tag(kid.tag) in WordTags for kid in node)):
                self.nbad += 1
                print node
                break
    
    def output(self):
        print 'rules (H1 H2...) = %d/%d=%.2f%%' % (self.nbad,self.nderivs,
                                                   self.nbad/float(self.nderivs)*100.0)
