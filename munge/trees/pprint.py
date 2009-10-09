from itertools import izip, count

def intersperse(l, spacer=", "):
    for i in xrange(len(l)-1, 0, -1):
        l.insert(i, spacer)
    return l
    
def default_node_repr(node):
    if node.is_leaf():
        return "%s %s" % (node.tag, node.lex)
    else:
        return "%s" % node.tag
    
def aug_node_repr(node):
    if node.is_leaf():
        return "%s {%s} %s" % (node.tag, node.category, node.lex)
    else:
        return "%s {%s}" % (node.tag, node.category)

LeafCompressThreshold = 3 # Nodes with this number of all-leaf children will be printed on one line
def pprint(node, level=0, sep='   ', newline='\n', node_repr=default_node_repr, reduced_leaves=False):
    out = []
    if level == 0: 
        out.append('(')
    else: 
        out.append( sep * level )
    
    if node.is_leaf():
        if reduced_leaves:
            out.append(node_repr(node))
        else:
            out.append("(%s)" % node_repr(node))
    else:
        # special case for nodes with all-leaf children
        if node.count() <= LeafCompressThreshold and all(kid.is_leaf() for kid in node):
            out.append( "(%s %s)" % 
                (node_repr(node), 
                ' '.join([pprint(child, 0, sep, '', node_repr, reduced_leaves=True) for child in node])) )
        else:
            out.append( "(%s%s" % (node_repr(node), newline) )
            out += intersperse([pprint(child, level+1, sep, newline, node_repr) for child in node], newline)
            out.append( ")" )

    if level == 0: 
        out.append(')')
        
    return ''.join(out)
        
if __name__ == '__main__':
    from munge.penn.parse import *
    import sys
    
    trees = parse_tree(sys.stdin.read())
    for tree in trees:
        print pprint(tree, sep='  ')
        print