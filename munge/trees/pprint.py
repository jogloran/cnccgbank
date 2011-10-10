from munge.util.list_utils import intersperse
    
def default_node_repr(node, compress=False):
    if hasattr(node, 'category') and node.category is not None:
        if node.is_leaf():
            return "%s {%s} %s" % (node.tag, node.category, node.lex)
        else:
            return "%s {%s}" % (node.tag, node.category)
    else:
        if node.is_leaf():
            return "%s %s" % (node.tag, node.lex)
        else:
            return "%s" % node.tag
            
from munge.util.colour_utils import codes
LeafCompressThreshold = 3 # Nodes with this number of all-leaf children will be printed on one line
def pprint_with(node_repr, open='(', close=')', bracket_outermost=True, do_reduce=True):
    single_node_template = open + '%s' + close
    multi_node_template  = open + '%s %s' + close
    
    def base_pprint(node, level=0, sep='   ', newline='\n', detail_level=-1, reduced_leaves=False, focus=None, focused=False, **kwargs):
        out = []
        
        if bracket_outermost and level == 0:
            out.append(open)
        else: 
            out.append( sep * level )
            
        if focus and (focus is node):
            focused = True

        if focused:
            out.append(codes['bggreen'])
            
        reached_detail_level = level==detail_level
    
        if node.is_leaf() or reached_detail_level:
            if reduced_leaves:
                out.append(node_repr(node, compress=reached_detail_level))
            else:
                out.append(single_node_template % node_repr(node, compress=reached_detail_level))
        else:
            # special case for nodes with all-leaf children
            if do_reduce and node.count() <= LeafCompressThreshold and all(kid.is_leaf() for kid in node):
                out.append( multi_node_template % 
                    (node_repr(node), 
                    ' '.join([base_pprint(child, 0, sep, '', reduced_leaves=True, detail_level=detail_level, 
                        focus=focus, focused=focused) for child in node])) )
            else:
                out.append( "%s%s%s" % (open, node_repr(node), newline) )
                out += intersperse([base_pprint(child, level+1, sep, newline, detail_level=detail_level,
                    focus=focus, focused=focused) for child in node], newline)
                out.append( close )

        if bracket_outermost and level == 0:
            out.append(close)
            
        # only reset colour sequences when we finish recursion on the focus node
        if focus and (focus is node):
            out.append(codes['reset'])
        
        return ''.join(out)
        
    return base_pprint

pprint = pprint_with(default_node_repr)

if __name__ == '__main__':
    from munge.penn.parse import *
    import sys

    trees = parse_tree(sys.stdin.read(), AugmentedPennParser)
    for tree in trees:
        print pprint(tree, sep='  ')
        print
