from munge.trees.traverse import text_in_span, text

from munge.trees.traverse import leaves, get_leaf
from munge.util.list_utils import is_sublist
from munge.ccg.nodes import Node, Leaf
from munge.quote.base import BaseQuoter

def make_open_quote_leaf(q, double=True):
    if q and not q.is_leaf():
        q = q.lch
        
    lex = "``" if double else "`"
    return Leaf('LQU', 'LQU', 'LQU', lex, 'LQU', q)
    
def make_closed_quote_leaf(q, double=True):
    lex = "''" if double else "'"
    return Leaf('RQU', 'RQU', 'RQU', lex, 'RQU', q)

class SpanQuoter(BaseQuoter):
    def attach_quotes(self, deriv, span_begin, span_end, quote_type, higher, quotes):
        do_left = quotes in ("both", "left")
        do_right = quotes in ("both", "right")
        double = (quotes == "``")
        
        first_index = 0 if (span_begin is None) else span_begin
        last_index = 0 if (span_end is None) else span_end
        
        leaf_count = len(list(leaves(deriv)))
        quoted_text = list(text_in_span(deriv, first_index, (leaf_count - last_index)))
        
        if (first_index is not None) or (last_index is not None):
            if higher == "left":
                if do_right:
                    deriv = self.insert_quote(deriv, tokens=quoted_text, at=span_end, quote="end", double=double)
                if do_left:
                    deriv = self.insert_quote(deriv, tokens=quoted_text, at=span_begin, quote="begin", double=double)
            elif higher == "right":
                if do_left:
                    deriv = self.insert_quote(deriv, tokens=quoted_text, at=span_begin, quote="begin", double=double)
                if do_right:
                    deriv = self.insert_quote(deriv, tokens=quoted_text, at=span_end, quote="end", double=double)
                    
        quote_indices = []
        if (span_begin is not None) and do_left:
            quote_indices.append(span_begin)
        else:
            quote_indices.append( None ) 
            
        if (span_end is not None) and do_right:
            quote_indices.append(leaf_count - span_end - 1)
        else:
            quote_indices.append( None )
            
        return deriv, quote_indices
        
    def insert_quote(self, deriv, tokens, at, quote, double):
        if quote == "begin": direction = "forwards"
        elif quote == "end": direction = "backwards"
        
        node = get_leaf(deriv, at, direction)
        
        if (at is not None) and node:
            if quote == "end": # Process absorbed punctuation
                if self.punct_class:
                    node = self.punct_class.process_punct(deriv, node, at)
            
            if node and is_sublist(smaller=text(node), larger=tokens):
                attachment_node = node
                
                while (attachment_node.parent and is_sublist(smaller=text(attachment_node.parent),
                                                             larger=tokens)):
                    attachment_node = attachment_node.parent
                    
                prev_parent = attachment_node.parent
                was_left_child = (attachment_node.parent) and (attachment_node.parent.lch is attachment_node)
                
                if quote == "begin":
                    new_node = Node(attachment_node.cat, 0, 2, 
                                    parent=None, lch=make_open_quote_leaf(None, double),
                                    rch=attachment_node)
                elif quote == "end":
                    new_node = Node(attachment_node.cat, 0, 2,
                                    parent=None, lch=attachment_node,
                                    rch=make_closed_quote_leaf(None, double))
                                    
                if prev_parent:
                    if was_left_child:
                        prev_parent.lch = new_node
                    else:
                        prev_parent.rch = new_node
                else:
                    return new_node # Replace the old root

        return deriv