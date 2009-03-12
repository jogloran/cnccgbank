from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix
from munge.cats.cat_defs import SbNPbSbNP
from munge.trees.traverse import leaves

class FixAdverbs(Fix):
    def pattern(self):
        return leaves
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    @staticmethod
    def is_modifier_category(cat):
        return cat.is_complex() and cat.left == cat.right
    
    @classmethod
    def is_candidate(cls, node):
        if node.parent and node.parent.count() > 1:
            l, r, p = node.parent[0], node.parent[1], node.parent
            L, R, P = (n.category for n in (l, r, p))
            
            if (cls.is_modifier_category(R) and
                L.is_complex() and
                r is node and 
                L == R.left): return True
        
        return False
        
    @staticmethod
    def fix_category(node):
        print "FIX: %s" % node
        A = node.parent[0].category.left
        node.category = A|A
        
    def fix(self, node):
        if self.is_candidate(node):
            self.fix_category(node)