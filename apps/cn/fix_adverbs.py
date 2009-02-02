from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix
from munge.cats.cat_defs import SbNPbSbNP

class FixAdverbs(Fix):
    def pattern(self):
        return r'* < {/VV/ . /AS/}'
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix(self, node):
        node[1].category = SbNPbSbNP