from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix
from munge.cats.cat_defs import SbNPbSbNP
from munge.trees.traverse import leaves
from apps.cn.fix_utils import *
from munge.cats.cat_defs import N, NP, SfS
import munge.penn.aug_nodes as A
from apps.util.echo import echo

import copy

def _insert_unary(new_P_cat, new_N_cat):
    def _fix(self, node, p, l, r):
        new_N = copy.copy(p)
        new_N.category = new_N_cat

        pp = p.parent

        if pp:
            replace_kid(pp, p, A.Node(new_P_cat, p.tag, [new_N]))
        else:
            return A.Node(new_P_cat, p.tag, [new_N])
            
    return _fix

class FixNP(Fix):
    def pattern(self):
        return [
            (r'@"NP"=P <1 @/\/N$/a=L <2 @"NP"=R', self.fix1),
            (r'@"NP"=P <1 @"N/N"=L <2 @"N"=R', self.fix_np),
            (r'@"S/S"=P <1 @"NP"=L <2 @"NP"=R', self.fix_topicalised_apposition),
        ]
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix1(self, node, p, l, r):
        r.category = N
        
    # NP < N/N N  ---> NP < N < N/N N
    fix_np = _insert_unary(NP, N)
    # S/S < NP NP ---> S/S < NP < NP NP
    fix_topicalised_apposition = _insert_unary(SfS, NP)
