# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.util.config import config
from munge.util.list_utils import intersperse
from munge.util.colour_utils import codes

use_colour = config.use_colour
    
def default_node_repr(node, compress=False, **kwargs):
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
            
LeafCompressThreshold = 3 # Nodes with this number of all-leaf children will be printed on one line
def pprint_with(node_repr, open='(', close=')', bracket_outermost=True, do_reduce=True):
    single_node_template = open + '%s' + close
    multi_node_template  = open + '%s %s' + close
    
    def base_pprint(node, level=0, sep='   ', newline='\n', detail_level=-1, 
                    reduced_leaves=False, focus=None, focused=False, 
                    gloss_text=None, gloss_iter=None, **kwargs):
        '''Prertty prints _node_.
sep: a string to use to indent a line by one level
newline: a string to use at the end of each line
detail_level: a depth, beyond which node_repr is called with kwarg compress=True
reduced_leaves: whether to use reduced leaves
focus: a node, under which a highlighting colour is applied
focused: whether a highlighting colour is being applied
gloss_iter: an iterable of gloss words
'''
        out = []
        
        if gloss_text is not None and gloss_iter is None:
            gloss_iter = iter(gloss_text)

        if bracket_outermost and level == 0:
            out.append(open)
        else: 
            out.append( sep * level )
            
        if focus and (focus is node):
            focused = True

        if focused and use_colour:
            out.append(codes['bggreen'])
            
        reached_detail_level = level==detail_level
    
        if node.is_leaf() or reached_detail_level:
            leaf_repr = node_repr(node, compress=reached_detail_level, gloss_iter=gloss_iter)
            
            if reduced_leaves:
                out.append(leaf_repr)
            else:
                out.append(single_node_template % leaf_repr)
        else:
            # special case for nodes with all-leaf children
            if do_reduce and node.count() <= LeafCompressThreshold and all(kid.is_leaf() for kid in node):
                # set level=0 so the text is not indented
                kid_reprs = [base_pprint(child, 0, sep, '', 
                             reduced_leaves=True, detail_level=detail_level, 
                             focus=focus, focused=focused, gloss_iter=gloss_iter) for child in node]
                             
                out.append( multi_node_template % (node_repr(node, gloss_iter=gloss_iter), ' '.join(kid_reprs)) )
            else:
                out.append( "%s%s%s" % (open, node_repr(node, gloss_iter=gloss_iter), newline) )
                out += intersperse([base_pprint(child, level+1, sep, newline, detail_level=detail_level,
                    focus=focus, focused=focused, gloss_iter=gloss_iter) for child in node], newline)
                out.append( close )

        if bracket_outermost and level == 0:
            out.append(close)
            
        # only reset colour sequences when we finish recursion on the focus node
        if focus and (focus is node) and use_colour:
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
