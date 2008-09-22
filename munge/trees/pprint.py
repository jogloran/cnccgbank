from itertools import izip, count

def intersperse(l, spacer=", "):
    for i in xrange(len(l)-1, 0, -1):
        l.insert(i, spacer)
    return l
    
def default_node_repr(node):
    return "(%s %s)" % (node.tag, node.lex)

def pprint(node, level=0, sep='   ', newline='\n', node_repr=default_node_repr):
    out = []
    if level == 0: 
        out.append('(')
    else: 
        out.append( sep * level )
    
    if node.is_leaf():
        out.append(node_repr(node))
    else:
        out.append( "(%s%s" % (node.tag, newline) )
        out += intersperse([pprint(child, level+1, sep, newline, node_repr) for child in node], newline)
        out.append( ")" )

    if level == 0: 
        out.append(')')
        
    return ''.join(out)
        
if __name__ == '__main__':
    from munge.penn.parse import *
    t=parse_tree(open('twsj').read())[0]
    print pprint(t, sep='   ')