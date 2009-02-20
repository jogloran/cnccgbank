from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, find_first
from munge.penn.aug_nodes import Node
from apps.cn.output import OutputDerivation
from apps.cn.fix import Fix
from munge.trees.pprint import pprint, aug_node_repr
from munge.util.tgrep_utils import get_first
from munge.cats.cat_defs import *

class FixExtraction(Fix):
    def pattern(self): 
        return {
            r'* < { /CP/ < {/WHNP-\d/ $ {/CP/ << {/NP-SBJ/ < "-NONE-"}}}}': self.fix_subject_extraction,
            r'* < { /CP/ < {/WHNP-\d/ $ {/CP/ << {/NP-OBJ/ < "-NONE-"}}}}': self.fix_object_extraction
        }
    
    def __init__(self, outdir):
        Fix.__init__(self, outdir)
        
    def remove_null_element(self, node):
        # Remove the null element WHNP and its trace -NONE- '*OP*' and shrink tree
        node[0] = node[0][1]
        
    def relabel_relativiser(self, node):
        # Relabel the relativiser category (NP/NP)\S to (NP/NP)\(S|NP)
        relativiser = node[0][1]
        relativiser.category = relativiser.parent.category | node[0][0].category
        
    def typeraise(self, node):
        typeraised_node = Node(S/(S|NP), node.tag, [ node[0] ], node)
        node[0] = typeraised_node
        
    def fcomp_children(self, node):
        print pprint(node, node_repr=aug_node_repr)
        print node[0].category, ",", node[1].category
        return node[0].category.left / node[1].category.right
        
    def fix_categories_starting_from(self, node, until):
        while (node is not until) and node.parent:
            node.category = node[1].category
            node = node.parent
            
        # node == until or node is root
        node.category = self.fcomp_children(node)
            
    def fix_subject_extraction(self, node):
        print "Fixing subject extraction: %s" % node
        self.remove_null_element(node)
        
        # Find and remove the trace
        trace_NP_parent = get_first(node, r'* < { * < { /NP-SBJ/ < "-NONE-" } }')
        trace_NP_parent[0] = trace_NP_parent[0][1]
        
        self.relabel_relativiser(node)
        
    def fix_object_extraction(self, node):
        print "Fixing object extraction: %s" % node
        self.remove_null_element(node)
        
        # Find and remove the trace
        trace_NP_parent = get_first(node, r'* < { * < { /NP-OBJ/ < "-NONE-" } }')
        trace_NP_parent[1] = trace_NP_parent[1][0]

        # For object extraction, find and type-raise the subject NP
        NP_node = get_first(node, r'* < { /NP/ > /IP/ }')
        self.typeraise(NP_node)
        
        # node[0][0] is the CP node
        self.fix_categories_starting_from(trace_NP_parent, until=node[0][0])
        
        self.relabel_relativiser(node)