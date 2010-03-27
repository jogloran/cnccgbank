from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep
from munge.cats.cat_defs import S, SbNPbSbNP, featureless, Sdcl
from munge.trees.traverse import leaves
from munge.cats.nodes import FORWARD, BACKWARD
from munge.util.err_utils import debug

from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix

class FixAdverbs(Fix):
    def pattern(self):
        return leaves
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    @staticmethod
    def is_modifier_category(cat):
        return cat.is_complex() and cat.left == cat.right
    
    @staticmethod
    def is_bxcomp_candidate(L, R, P):
        # Y/Z X\Y -> X/Z
        try:
            # Only generalise result categories rooted in S.
            # Otherwise, we get spurious generalisations such as N/N (N/N)\(N/N) (1:8(4))
            if not L.left.left.equal_respecting_features(Sdcl): return False
            
            return (R.left.left == L.left and # Y unifies
                    P.right == L.right and # Z unifies
                    P.left == R.left.left and # X unifies
                    L.direction == FORWARD and
                    R.direction == BACKWARD and
                    P.direction == FORWARD)
        except AttributeError:
            return False
    
    @staticmethod
    def is_bxcomp2_candidate(L, R, P):
        # (Y/Z)/W X\Y -> (X/Z)/W
        try:
            # Only generalise result categories rooted in S
            if not L.left.left.left.equal_respecting_features(Sdcl): return False
            
            return (R.left.left.left == L.left.left and # Y unifies
                    P.right == L.right and # W unifies
                    R.left.left.left == P.left.left and # X unifies
                    P.left.right == L.left.right and # Z unifies
                    L.left.direction == FORWARD and
                    R.direction == BACKWARD and
                    P.direction == FORWARD)
        except AttributeError:
            return False
    
    @classmethod
    def do_fix(C, node):
        def bxcomp(L, R, P):
            A = featureless(L.left)
            return A|A
        def bxcomp2(L, R, P):
            A = featureless(L.left.left)
            return A|A
            
        if node.parent and node.parent.count() > 1:
            l, r, p = node.parent[0], node.parent[1], node.parent
            L, R, P = (n.category for n in (l, r, p))
            
            if ((not any(
                    p.tag.startswith(cand) for cand in ('VSB',))) and
                C.is_modifier_category(R) and
                L.is_complex() and
                r is node):
                
                if C.is_bxcomp2_candidate(L, R, P):
                    node.category = bxcomp2(L, R, P)
                    debug("Generalised %s to %s", R, node.category)
                elif C.is_bxcomp_candidate(L, R, P):
                    node.category = bxcomp(L, R, P)
                    debug("Generalised %s to %s", R, node.category)
        
    def fix(self, node):
        self.do_fix(node)