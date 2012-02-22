# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.cats.cat_defs import S, featureless, Sdcl
from munge.trees.traverse import leaves
from munge.cats.nodes import FORWARD, BACKWARD
from apps.cn.fix_rc import is_rooted_in
from munge.util.err_utils import debug

from apps.cn.fix import Fix
from munge.util.config import config

use_sb_alias = config.use_sb_alias

def is_modifier_category(cat):
    return cat.is_complex() and cat.left == cat.right

class FixAdverbs(Fix):
    def pattern(self):
        return leaves
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
    
    @staticmethod
    def is_bxcomp_candidate(L, R, P):
        # Y/Z X\Y -> X/Z
        try:
            # Only generalise result categories rooted in S.
            # Otherwise, we get spurious generalisations such as N/N (N/N)\(N/N) (1:8(4))
            if not is_rooted_in(Sdcl, L, respecting_features=True): return False
            if not is_rooted_in(S, R, respecting_features=True): return False
            
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
            if not is_rooted_in(Sdcl, L, respecting_features=True): return False
            if not is_rooted_in(S, R, respecting_features=True): return False
            
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
            
            if (not p.tag.startswith('VSB') and
                is_modifier_category(R) and
                L.is_complex() and
                r is node):
                
                if C.is_bxcomp2_candidate(L, R, P):
                    node.category = bxcomp2(L, R, P)
                    debug("Generalised %s to %s", R, node.category)
                elif C.is_bxcomp_candidate(L, R, P):
                    node.category = bxcomp(L, R, P)
                    debug("Generalised %s to %s", R, node.category)
        
    def fix(self, node):
        # Add ~SB alias
        global use_sb_alias
        if use_sb_alias and str(node.category) == '(S[dcl]\\NP)/(S[dcl]\\NP)' and node.tag.startswith('SB'):
            node.category.alias = "SB"
            
        self.do_fix(node)