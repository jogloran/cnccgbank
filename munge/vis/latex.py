from munge.cats.trace import analyse
from munge.trees.traverse import pairs_postorder, leaves
from itertools import groupby
from apps.ccgdraw import sanitise_category

def min_leaf_id(node, root):
    cur = node
    while not cur.is_leaf():
        cur = cur[0]
        
    # cur is the left corner of _node_
    
    for leaf_id, leaf in enumerate(leaves(root)):
        if leaf is cur:
            return leaf_id
            
def nodes_with_depth(node, depth=0):
    yield (deriv, depth)
    for kid in deriv:
        for kid_node in nodes_with_depth(kid, depth+1):
            yield (kid_node, depth+1)

def group(rows):
    output = []
    subrow = []
    last_leftmost = -1
    last_span = -1

    for leftmost_leaf_id, cat, comb, span in sorted(rows, key=lambda (a,b,c,d):(d,a)):
        if last_leftmost >= leftmost_leaf_id:
            output.append(subrow)
            subrow = [ (leftmost_leaf_id, cat, comb, span) ]
        else:
            subrow.append( (leftmost_leaf_id, cat, comb, span) )
            
        last_leftmost = leftmost_leaf_id
        last_span = span
        
    if subrow:
        output.append(subrow)
        
    return output
    
tails = {
    'fwd_appl': 'fapply',
    'bwd_appl': 'bapply',
    'fwd_comp': 'fcomp',
    'bwd_comp': 'bcomp',
    'fwd_xcomp': 'fxcomp',
    'bwd_xcomp': 'bxcomp',
    'fwd_subst': 'fsubst',
    'bwd_subst': 'bsubst',
    'fwd_xsubst': 'fxsubst',
    'bwd_xsubst': 'bxsubst',
    'fwd_typeraise': 'ftype',
    'bwd_typeraise': 'btype',
}
def ccg2latex(node):
    def comb_symbol(comb):
        return tails.get(comb, 'uline')
        
    out = ['\deriv{%d}{' % node.leaf_count()]
    rows = []
    
    out.append( (' & '.join(("\\cjk{%s}"%leaf.lex) for leaf in leaves(node))) + '\\\\' )
    out.append( ' & '.join(["\uline{1}"] * node.leaf_count()) + '\\\\' )
    out.append( (' & '.join(("\\cf{%s}"%sanitise_category(str(leaf.cat))) for leaf in leaves(node))) + '\\\\' )
    
    for l, r, p in pairs_postorder(node):
        rows.append( (min_leaf_id(p, node), p.cat, analyse(l.cat, r and r.cat, p.cat), p.leaf_count()) )
        
    grouped_subrows = group(rows)
        
    for subrows in grouped_subrows:
        subline = []
        subout = []
        last_span = 0
        for leftmost_leaf_id, cat, comb, span in subrows:
            subline.append( "&"*(leftmost_leaf_id - last_span) + ("\%s{%s}" % (comb_symbol(comb), span)) )
            subout.append( "&"*(leftmost_leaf_id - last_span) + ("\mc{%d}{%s}" % (span, sanitise_category(str(cat)))) )
            
            last_span = leftmost_leaf_id+span-1

        out.append(' '.join(subline) + '\\\\')
        out.append(' '.join(subout) + '\\\\')

#    print ' '.join(out)
    out.append('}')
    return '\n'.join(out)