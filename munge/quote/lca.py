# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.ccg.nodes import Leaf, Node
from munge.quote.base import BaseQuoter
from munge.quote.utils import make_open_quote_leaf, make_closed_quote_leaf
from munge.trees.traverse import leaves, get_leaf
from munge.cats.paths import lca

class LCAQuoter(BaseQuoter):
    def attach_quotes(self, deriv, span_begin, span_end, quote_type, higher, quotes):
        leaf_count = len(list(leaves(deriv)))
        
        first_index = 0 if (span_begin is None) else span_begin
        last_index =  0 if (span_end is None)   else span_end
        
        begin_node = get_leaf(deriv, first_index, "forwards")
        end_node = get_leaf(deriv, last_index, "backwards")
        
        if end_node:
            end_node = self.punct_class.process_punct(deriv, end_node, span_end)
            
        lca_node = lca(begin_node, end_node)
        if lca_node:
            deriv = self.insert_quotes(deriv, lca_node, higher)
            
        quote_indices = [None, None]
        for index, leaf in enumerate(leaves(deriv)):
            if str(leaf.cat) == 'LQU':
                quote_indices[0] = index
            elif str(leaf.cat) == 'RQU':
                quote_indices[1] = index - 2
                
        return deriv, quote_indices
        
    def insert_quotes(self, deriv, attachment_node, higher):
        open_quote_leaf = make_open_quote_leaf(None)
        closed_quote_leaf = make_closed_quote_leaf(None)

        old_subtree = attachment_node.clone()
        
        if higher == "left":
            right_child = Node(attachment_node.cat, 0, 2, None,
                               old_subtree,
                               closed_quote_leaf)
            new_node    = Node(attachment_node.cat, 0, 2, None,
                               open_quote_leaf,
                               right_child)
        elif higher == "right":
            left_child  = Node(attachment_node.cat, 0, 2, None,
                               open_quote_leaf,
                               old_subtree)
            new_node    = Node(attachment_node.cat, 0, 2, None,
                               left_child,
                               closed_quote_leaf)
                            
                            
        prev_parent = attachment_node.parent
        was_left_child = (prev_parent is not None) and (prev_parent.lch is attachment_node)
        
        if prev_parent:
            if was_left_child:
                prev_parent.lch = new_node
            else:
                prev_parent.rch = new_node
                
        else: # Replace old root
            return new_node
            
        return deriv
        
