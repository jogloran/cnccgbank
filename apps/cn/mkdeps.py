# coding=utf-8
from apps.util.config import config
config.set(show_vars=True) # override show_vars. must come before cats.nodes import
    
from itertools import izip
from copy import deepcopy

from munge.proc.filter import Filter
from munge.cats.headed.parse import parse_category
from munge.cats.trace import analyse
from munge.trees.traverse import leaves, pairs_postorder, nodes
from munge.util.iter_utils import flatten, seqify
from munge.util.err_utils import debug, warn
from munge.trees.pprint import pprint

from apps.cn.mkmarked import is_modifier

def copy_vars(frm, to):
    for (frms, tos) in izip(frm.nested_compound_categories(), to.nested_compound_categories()):
        tos.slot = frms.slot

def update_with_fresh_var(node, replacement):
    # change all occurrences of vars with the same var name as c to the same fresh var
    to_replace = node.cat.slot.var
    for sub in node.cat.nested_compound_categories():
        if sub.slot.var == to_replace:
            sub.slot = replacement
            
def no_unassigned_variables(cat):
    for subcat in cat.nested_compound_categories():
        if subcat.slot.var == '?': return False
    return True
    
fresh_var_id = 1
def fresh_var(prefix='F'):
    global fresh_var_id
    ret = prefix + str(fresh_var_id)
    fresh_var_id += 1
    return ret

unanalysed = set()
def mkdeps(root):
    global unanalysed

    for l, r, p in pairs_postorder(root):
        L, R, P = map(lambda x: x and x.cat, (l, r, p))
        comb = analyse(L, R, P)
        if not comb: debug("Unrecognised rule %s %s -> %s", L, R, P)
        
        if config.debug:
            debug("%s %s %s", L, R, P)
            debug(str(comb))

        if comb == 'fwd_appl': # X/Y Y
            unifier = unify(L.right, R, copy_to=RIGHT)
            p.cat = L.left

        elif comb == 'bwd_appl': # Y X\Y
            unifier = unify(L, R.right, copy_to=LEFT)
            p.cat = R.left

        elif comb == 'fwd_comp': # X/Y Y/Z -> X/Z
            P.slot = L.slot # lexical head comes from R (Y/Z)

            unifier = unify(L.right, R.left, copy_to=RIGHT)
            p.cat._left = L.left
            p.cat._right = R.right
            
        elif comb == 'bwd_comp': # Y\Z X\Y -> X\Z
            P.slot = R.slot # lexical head comes from L (Y\Z)
            
            unifier = unify(R.right, L.left)
            p.cat._left = R.left
            p.cat._right = L.right

        elif comb == 'conjoin': # X X[conj] -> X
            copy_vars(frm=R, to=P)

            P.slot = deepcopy(P.slot)
            update_with_fresh_var(p, P.slot)
            P.slot.head.lex = list(flatten((L.slot.head.lex, R.slot.head.lex)))
            
            unifier = unify(L, R, ignore=True, copy_to=RIGHT, copy_vars=False) # unify variables only in the two conjuncts
            for (dest, src) in unifier:
                old_head = src.slot.head
                
                # look under L and transform all references to 'Z' to references to the 'Z' inside R                
                for node in nodes(l):
                    for subcat in node.cat.nested_compound_categories():
                        if subcat.slot.head is old_head:
                            subcat.slot.head = dest.slot.head

            unify(P, R, ignore=True, copy_to=RIGHT) # unify variables only in the two conjuncts

        elif comb in ('conj_absorb', 'conj_comma_absorb', 'funny_conj'): # conj X -> X[conj]
            copy_vars(frm=R, to=P)
            unify(P, R, copy_to=RIGHT) # R.slot.head = P.slot.head
        
        elif comb == 'nongap_topicalisation': # {N, NP, S[dcl], QP}x -> [Sy/Sy]x
            P.slot = L.slot
            P.right.slot.var = fresh_var()
            P.left.slot = P.right.slot
            
        elif comb in ('np_gap_topicalisation', 's_gap_topicalisation', 'qp_gap_topicalisation'): # NPx -> [ Sy/(Sy/NPx)y ]y
            P.right.right.slot = L.slot
            P.slot.var = fresh_var()
            P.left.slot = P.right.left.slot = P.right.slot = P.slot
            
        elif comb == 'subject_prodrop': # (S[dcl]y\NPx)y -> S[dcl]y | [(S[dcl]y\NPx)y/NPz]y -> (S[dcl]y/NPz)y
            if P == parse_category(r'S[dcl]'):
                P.slot = L.slot
            elif P == parse_category(r'S[dcl]/NP'):
                P.slot = P.left.slot = L.slot
                P.right.slot = L.right.slot
            else:
                warn("Invalid parent category %s for subject prodrop.", P)
            
        elif comb == 'fwd_xcomp': # X/Y Y\Z -> X/Z
            P.slot = R.slot
            
            unifier = unify(L.right, R.left)
            p.cat._left = L.left
            p.cat._right = R.right

        elif comb == 'bwd_xcomp': # Y/Z X\Y -> X/Z
            P.slot = L.slot
            
            unifier = unify(L.left, R.right, copy_to=LEFT)
            p.cat._left = R.left
            p.cat._right = L.right
        elif comb == 'bwd_r1xcomp': # (Y/Z)/W X\Y -> (X\Z)/W
            # TODO: where should P's lexical head come from? L or R?
            
            unifier = unify(L.left.left, R.right)
            p.cat._left._left = R.left
            p.cat._left._right = L.left.right
            p.cat._right = L.right

        elif comb in ('fwd_raise', 'bwd_raise'): # Xx -> [ Tf|(Tf|Xx)f ]f
            P.slot.var = fresh_var()

            P.right.left.slot = P.left.slot = P.right.slot = P.slot
            P.right.right.slot = L.slot

            unifier = unify(L, P.right.right)

        elif comb == 'np_typechange':
            P.slot = L.slot # = copy_vars
            unifier = unify(P, L)
        
        elif comb == 'null_relativiser_typechange': # Xy -> (Nf/Nf)y
            P.slot = L.slot
            
            if P == parse_category(r'N/N'):
                P.left.slot.var = fresh_var()
                
                P.right.slot = P.left.slot
            elif P == parse_category(r'(N/N)/(N/N)'):
                P.left.slot.var = fresh_var()
                P.left.left.slot.var = fresh_var(prefix="G")
                
                P.left.right.slot = P.left.left.slot
                P.right.slot = P.left.slot
            
        elif comb == 'l_punct_absorb':
            p.cat = R
            
        elif comb == 'r_punct_absorb':
            p.cat = L

        elif R and L == R: # VCD (stopgap)
            unify(P, R) # assume VCD is right headed
            p.cat = R

        else:
            debug('Unhandled combinator %s (%s %s -> %s)', comb, L, R, P)
            unanalysed.add(comb)
            
            P.slot = L.slot
            
        if config.debug:
            debug("> %s" % p.cat)
            debug('---')
            
            assert no_unassigned_variables(p.cat), "Unassigned variables in %s" % p.cat
        
#        print pprint(root)

    # Collect deps from arguments
    deps = []
    for l in leaves(root):
        if config.debug: debug("%s %s", l.lex, l.cat)
        C = l.cat
        while not C.is_leaf():
            arg = C.right
            if arg.slot.head.filler:
                deps.append( (C.slot.head.lex, arg.slot.head.lex) )
            C = C.left

    # Produce dep pairs
    result = set()
    for depl, depr in deps:
        for sdepl in set(seqify(depl)):
            for sdepr in set(seqify(depr)):
                result.add( (sdepl, sdepr) )
                
    return result

LEFT, RIGHT = 1, 2
class UnificationException(Exception): pass
def unify(L, R, ignore=False, copy_to=LEFT, copy_vars=True):
    assgs = []
    
    for (Ls, Rs) in izip(L.nested_compound_categories(), R.nested_compound_categories()):
        if Ls.slot.is_filled() and Rs.slot.is_filled():
            if (not ignore) and Ls.slot.head.lex != Rs.slot.head.lex:
                raise UnificationException('%s and %s both filled' % (Ls, Rs))

        elif Ls.slot.is_filled():
            Rs.slot.head.lex = Ls.slot.head.lex
            Rs.slot.head.filler = L

        elif Rs.slot.is_filled():
            Ls.slot.head.lex = Rs.slot.head.lex
            Ls.slot.head.filler = R

        else: # both slots are variables, need to unify variables
            # print "vars Ls: %s Rs: %s" % (Ls, Rs)
            # print "vars L: %s R: %s" % (L, R)
            #Rs.slot.head = Ls.slot.head # Direction matters, unification is asymmetric
#            if copy_to == LEFT:
            # we should be copying from modifiers to heads
#                if copy_vars: Ls.slot.head = Rs.slot.head
#                print "Lh done L head(%s) = R head(%s)" % (Ls.slot, Rs.slot)
                
#                assgs.append( (Ls, Rs) )
#            else: #elif L.is_modifier():
#            else:
#                if copy_vars: Rs.slot.head = Ls.slot.head
#                print "Rh done R head(%s) = L head(%s)" % (Rs.slot, Ls.slot)
                
#                assgs.append( (Rs, Ls) )
            if copy_vars: Rs.slot.head = Ls.slot.head
            assgs.append( (Rs, Ls) )
    return assgs

class MakeDependencies(Filter):
    def __init__(self, outdir):
        Filter.__init__(self)
        self.outdir = outdir

    def accept_derivation(self, bundle):
        deps = mkdeps(bundle.derivation)
        self.write_deps(deps)

    def output(self):
        pass

    def write_deps(self, deps):
        pass

    opt = '9'
    long_opt = 'mkdeps'

    arg_names = 'OUTDIR'

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError: pass
    
    from munge.ccg.parse import *
    from apps.cn.mkmarked import *

#    t=naive_label_derivation(parse_tree(open('final/chtb_0119.fid').readlines()[13]))
#    t=naive_label_derivation(parse_tree(open('apps/cn/tests/test1.ccg').readlines()[1]))
    file = "final/%s" % sys.argv[1]
    t=naive_label_derivation(parse_tree(open(file).readlines()[2*int(sys.argv[2])+1]))
    print t
    print "sent:"
    print "-----"
    print ' '.join(t.text())
    deps = mkdeps(t)
    
    print "deps:"
    print "-----"
    for l, r in deps: print "%s|%s" % (l, r)
    
    print "leaves:"
    print "-------"
    for leaf in leaves(t):
        print leaf.lex, leaf.cat
        
    print "unhandled combs:"
    print "----------------"
    for comb in unanalysed:
        print comb
        
    print "finished:"
    print pprint(t)
