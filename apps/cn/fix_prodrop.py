from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix

class FixProDrop(Fix):
    def pattern(self):
        return r'* < { * < ^"*pro*" }'
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix(self, node):
        node.kids.pop(0)
        
        # this step happens after fix_rc, and object extraction with subject pro-drop can
        # lead to a pro-dropped node like:
        #     S/(S\NP)
        #        |
        #       NP
        #        |
        #   -NONE- '*pro*'
        # In this case, we want to remove the whole structure
        if not node.kids:
            node = node.parent
            node.kids.pop(0)