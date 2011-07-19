from itertools import izip
from munge.util.err_utils import debug

def copy_vars(frm, to):
    '''Given two categories _frm_ and _to_, assumed to be the same modulo slots, overwrites the
slots of _to_ with those of _frm_.'''
    for (frms, tos) in izip(frm.nested_compound_categories(), to.nested_compound_categories()):
        tos.slot = frms.slot

def update_with_fresh_var(node, replacement):
    '''Where _node_ is a node, and C is its category, replaces all variables in sub-categories of C
with the same name as C's outermost variable with the slot _replacement_.'''
    # change all occurrences of vars with the same var name as c to the same fresh var
    to_replace = node.cat.slot.var
    for sub in node.cat.nested_compound_categories():
        if sub.slot.var == to_replace:
            sub.slot = replacement
            
def no_unassigned_variables(cat):
    '''Yields whether any sub-category inside category _cat_ has a slot without a variable.'''
    for subcat in cat.nested_compound_categories():
        if subcat.slot.var == '?': return False
    return True
    
fresh_var_id = 1
def fresh_var(prefix='F'):
    '''Returns a unique variable name with a given _prefix_.'''
    global fresh_var_id
    ret = prefix + str(fresh_var_id)
    fresh_var_id += 1
    return ret
    
class UnificationException(Exception): pass
def unify(L, R, ignore=False, copy_vars=True):
    assgs = []

    for (Ls, Rs) in izip(L.nested_compound_categories(), R.nested_compound_categories()):
        if Ls.slot.is_filled() and Rs.slot.is_filled():
            if (not ignore) and Ls.slot.head.lex != Rs.slot.head.lex:
                raise UnificationException('%s (%s) and %s (%s) both filled' % (Ls, Ls.slot, Rs, Rs.slot))

        elif Ls.slot.is_filled():
            debug('R %s <- L %s', Rs.slot, Ls.slot)
            
            Rs.slot.head.lex = Ls.slot.head.lex
            Rs.slot.head.filler = L
                    
            assgs.append( (Rs, Ls.slot.head.lex) )

        elif Rs.slot.is_filled():
            debug('L %s <- R %s', Ls.slot, Rs.slot)
                
            Ls.slot.head.lex = Rs.slot.head.lex
            Ls.slot.head.filler = R
                
            assgs.append( (Ls, Rs.slot.head.lex) )

        else: # both slots are variables, need to unify variables
            if Ls.slot == Rs.slot: continue

            debug('%s <-> %s (copy_vars=%s)', Ls.slot, Rs.slot, copy_vars)
            if copy_vars:
                Rs.slot.unify_heads(Ls.slot)

            assgs.append( (Rs, Ls) )

    return assgs
