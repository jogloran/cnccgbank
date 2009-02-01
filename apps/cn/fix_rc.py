from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix

class FixExtraction(Fix):
    def pattern(self): 
        return {
            r'/CP/ < {/WHNP-\d/ $ /CP/}': self.fix_DEC_case
        }
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix(self, node):
#        node.tag = 'HELLO'
        pass
        
    def fix_DEC_case(self, node):
        # Remove the null element WHNP and its trace -NONE- '*OP*'
        
        # Shrink tree
        
        # Find trace (is it subject, or object extraction?)
        
        # If object extraction, find and type-raise the subject NP
        
        # Remove trace and shrink tree
        # Relabel the S node to S/NP or S\NP
        
        # Relabel the relativiser category (NP/NP)\S to (NP/NP)\(S|NP)

        