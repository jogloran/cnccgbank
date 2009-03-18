from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix
from munge.cats.cat_defs import SbNPbSbNP
from munge.trees.traverse import leaves
from apps.cn.fix_utils import *
from munge.cats.cat_defs import N, NP
import munge.penn.aug_nodes as A

import copy

class FixNP(Fix):
    def pattern(self):
        return r'{ @"NP"=P <1 @"N/N"=L <2 @"N"=R } > *=PP'
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix(self, node, pp, p, l, r):
        new_N = copy.copy(p)
        new_N.category = N
        
        replace_kid(pp, p, A.Node(NP, p.tag, [new_N]))