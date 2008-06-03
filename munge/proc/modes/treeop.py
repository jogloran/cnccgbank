from munge.cats.nodes import NULL, APPLY, COMP, ALL
from munge.cats.trace import analyse

ModeTier = {
    NULL: 0, 
    APPLY: 1,
    COMP: 2, 
    ALL: 2
}

def mode_min(m1, m2):
    '''Returns the less permissive of two modes.'''
    return (m1 if ModeTier[m1] <= ModeTier[m2] else m2)
    
def zipped_each_slash(c1, c2):
    '''Given two mode vectors, allows them to be iterated over in parallel.'''
    if not (c1.is_complex() and c2.is_complex()): return
    
    yield c1, c1.label, c2, c2.label
    
    for bits in zipped_each_slash(c1.left, c2.left):
        yield bits
        
    for bits in zipped_each_slash(c1.right, c2.right):
        yield bits
        
def copy_modes(src, dst):
    '''Copies the modes on each slash of category _src_ to the corresponding slash
in category _dst_. Assumes that the two categories have the same slash count.'''
    for src_cat, _, dst_cat, _ in zipped_each_slash(src, dst):
        dst_cat.mode = src_cat.mode
        
def level_order_pairs(deriv):
    '''Given a CCG derivation, this returns its nodes in level order (all nodes from
level k+1 before all nodes from level k).'''
    queue = [ (deriv, None) ]
    result = []
    
    while queue:
        cur1, cur2 = queue[0]
        result.append( queue.pop(0) )
        
        if cur2 and (not cur2.is_leaf()):
            queue.append( (cur2.lch, cur2.rch) )
        if cur1 and (not cur1.is_leaf()):
            queue.append( (cur1.lch, cur1.rch) )
            
    return result[::-1]
        
def percolate(deriv):
    '''This percolates mode changes made at the leaves up the derivation tree.'''
    for lch, rch in level_order_pairs(deriv):
        parent = lch.parent # (== rch.parent)
        
        if rch or parent: # If lch is not the root
            comb = analyse(lch.cat, rch and rch.cat, parent.cat)
            
            if str(comb) == 'bwd_r1xcomp':
                # (Y/a)/Z X\Y -> (X/a)/Z
                #      ^  ^       ^   ^
                #      |  |_______|   |
                #      |______________|
                
                copy_modes(lch.cat, parent.cat)
                copy_modes(rch.cat.left, parent.cat.left.left)
                
            elif str(comb).endswith('comp'): # is composition
                lmode = lch.cat.mode # lch and rch are both necessarily compound
                rmode = rch.cat.mode
                # also check that lmode and rmode include composition
                # maybe issue message saying broken derivation otherwise

                parent.cat.mode = mode_min(lmode, rmode)

                if comb in ("fwd_comp", "fwd_xcomp"): # X/Y Y/Z -> X/Z or X/Y Y\Z -> X\Z
                    # copy modes from arguments to result
                    copy_modes(lch.cat.left, parent.cat.left)
                    copy_modes(rch.cat.right, parent.cat.right)
                elif comb in ("bwd_comp", "bwd_xcomp"): # Y\Z X\Y -> X\Z or Y/Z X\Y -> X/Z
                    copy_modes(rch.cat.left, parent.cat.left)
                    copy_modes(lch.cat.right, parent.cat.right)

            elif str(comb).endswith('type'): # is type raising
                # uses default mode (which is :all)
                pass
    
            elif str(comb) == "r_punct_absorb": # X ; -> X
                copy_modes(lch.cat, parent.cat)

            elif str(comb).endswith('absorb') or str(comb) == "conjoin":
                copy_modes(rch.cat, parent.cat)

            else: # assume application
                if comb == "fwd_appl": # X/Y Y -> X
                    copy_modes(lch.cat.left, parent.cat)
                elif comb == "bwd_appl": # Y X\Y -> X
                    copy_modes(rch.cat.left, parent.cat)
            
        
