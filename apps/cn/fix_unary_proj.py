from apps.cn.fix import Fix
from munge.trees.traverse import leaves

class FixUnaryProjections(Fix):
    def pattern(self, node):
        return leaves(node)
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix(self, node):
        node[1].category = SbNPbSbNP