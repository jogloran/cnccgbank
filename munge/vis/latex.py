# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.cats.trace import analyse
from munge.trees.traverse import pairs_postorder, leaves
from itertools import groupby, izip
from apps.util.latex.table import sanitise_category

def min_leaf_id(node, root):
    '''(Inefficiently) finds the leaf index of _node_ relative to _root_.'''
    cur = node
    while not cur.is_leaf():
        cur = cur[0]
        
    # cur is the left corner of _node_    
    for leaf_id, leaf in enumerate(leaves(root)):
        if leaf is cur:
            return leaf_id

def group(rows):
    '''Groups [row] into [ [row] ], where each sub-list contains reductions which can be rendered
in the same row.'''
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
    
arrows = {
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
    'fwd_raise': 'ftype',
    'bwd_raise': 'btype',
}
def ccg2latex(root, glosses=None):
    def comb_symbol(comb):
        return arrows.get(comb, 'uline')
    def cat_repr(cat):
        return sanitise_category(str(cat))
        
    out = ['\deriv{%d}{' % root.leaf_count()]    
    all_leaves = list(leaves(root))
    
    # lex line
    if glosses is not None:
        leaf_bits = ("\\glosN{%s}{%s}" % (leaf.lex, gloss) for (leaf, gloss) in izip(all_leaves, glosses))
    else:
        leaf_bits = (("\\cjk{%s}" % leaf.lex) for leaf in all_leaves)
    out.append(' & '.join(leaf_bits) + '\\\\')
    
    # underlines line
    out.append( ' & '.join(["\uline{1}"] * root.leaf_count()) + '\\\\' )
    # cats line
    out.append( (' & '.join(("\\cf{%s}"%cat_repr(leaf.cat)) for leaf in all_leaves)) + '\\\\' )
    
    rows = []
    for l, r, p in pairs_postorder(root):
        rows.append( (min_leaf_id(p, root), p.cat, analyse(l.cat, r and r.cat, p.cat), p.leaf_count()) )
        
    grouped_subrows = group(rows)
        
    for subrows in grouped_subrows:
        subline = []
        subout = []
        last_span = 0 # holds the index of the rightmost span in this row
        
        for leftmost_leaf_id, cat, comb, span in subrows:
            subline.append( "&"*(leftmost_leaf_id - last_span) + ("\%s{%s}" % (comb_symbol(comb), span)) )
            subout.append(  "&"*(leftmost_leaf_id - last_span) + ("\mc{%d}{%s}" % (span, cat_repr(cat))) )
            
            last_span = leftmost_leaf_id+span-1

        # write out underlines line
        out.append(' '.join(subline) + '\\\\')
        # write out cats line
        out.append(' '.join(subout) + '\\\\')

    out.append('}')
    return '\n'.join(out)