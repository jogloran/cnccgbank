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
    
def strip_index(s):
    return s.split('*')[0]
    
class UnificationException(Exception): pass
def unify(L, R, dependers, ignore=False, copy_vars=True, head=None):
    assgs = []

    for (Ls, Rs) in izip(L.nested_compound_categories(), R.nested_compound_categories()):
        if Ls.slot.is_filled() and Rs.slot.is_filled():
            if (not ignore) and Ls.slot.head.lex != Rs.slot.head.lex:
                raise UnificationException('%s (%s) and %s (%s) both filled' % (Ls, Ls.slot, Rs, Rs.slot))

        elif Ls.slot.is_filled():
            #debug('Rs %s R %s <- Ls %s L %s head %s' % (Rs, R, Ls, R, head))
            if Ls.slot.head.lex is None:
                debug("the head lex of %s is None", Ls)
            Rs.slot.head.lex = Ls.slot.head.lex
            Rs.slot.head.filler = L
            assgs.append( (Rs, Ls.slot.head.lex) )

        elif Rs.slot.is_filled():
            #debug('Ls %s L %s <- Rs %s R %s head %s' % (Ls, L, Rs, R, head))
            if Rs.slot.head.lex is None:
                debug("the head lex of %s is None", Rs)
            Ls.slot.head.lex = Rs.slot.head.lex
            Ls.slot.head.filler = R
            assgs.append( (Ls, Rs.slot.head.lex) )

        else: # both slots are variables, need to unify variables
            
            # Fake bidirectional unification for vars:
            # ----------------------------------------
            # If variable X has been unified with variable Y,
            # then things which used to point to the head of X should now point to 
            # the head of Y.
            # If a derivation has unifiers (A, B), (B, C), (C, v), then we need to
            # keep track of the depender variables [A, B].
            # When a variable unification (X, Y) happens, we go through the list of 
            # depender variables and rewrite any variable pointing to the head of
            # X to instead point to Y.
            for depender in dependers:
                if depender.head.lex == Rs.slot.head.lex:
                    depender.head = Ls.slot.head
            
            if copy_vars: Rs.slot.head = Ls.slot.head
            assgs.append( (Rs, Ls) )
            
            dependers.add(Rs.slot)

    return assgs
