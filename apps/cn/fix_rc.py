from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, find_first
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix
from munge.trees.pprint import pprint
from munge.util.tgrep_utils import get_first

class FixExtraction(Fix):
    def pattern(self): 
        return {
            r'* < { /CP/ < {/WHNP-\d/ $ {/CP/ << {/NP-SBJ/ < "-NONE-"}}}}': self.fix_subject_extraction,
            r'* < { /CP/ < {/WHNP-\d/ $ {/CP/ << {/NP-OBJ/ < "-NONE-"}}}}': self.fix_object_extraction
        }
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def fix(self, node):
#        node.tag = 'HELLO'
        pass
        
    def remove_null_element(self, node):
        # Remove the null element WHNP and its trace -NONE- '*OP*' and shrink tree
        node[0] = node[0][1]
        
    def relabel_relativiser(self, node):
        # Relabel the relativiser category (NP/NP)\S to (NP/NP)\(S|NP)
        relativiser = node[0][1]
        relativiser.category = relativiser.parent.category | node[0][0].category
            
    def fix_subject_extraction(self, node):
        self.remove_null_element(node)
        
        # For subject extraction, find the trace and remove it
        trace_NP_parent = get_first(node, r'* < { * < { /NP-SBJ/ < "-NONE-" } }')
        trace_NP_parent[0] = trace_NP_parent[0][1]
        
        self.relabel_relativiser(node)
        
    def fix_object_extraction(self, node):
        self.remove_null_element(node)
        
        # For subject extraction, find the trace and remove it
        trace_NP_parent = get_first(node, r'* < { * < { /NP-OBJ/ < "-NONE-" } }')
#        trace_NP_parent[0] = trace_NP_parent[0][1]

        # For object extraction, find and type-raise the subject NP
#        NP_node = list(find_first())
        
        self.relabel_relativiser(node)