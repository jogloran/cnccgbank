from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix

class FixTopicalisation(Fix):
    def pattern(self):
        # TODO:
        pass
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix(self, node):
        node.tag = 'HELLO'