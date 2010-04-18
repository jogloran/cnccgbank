# coding=utf-8
from apps.util.config import config
config.set(show_vars=True) # override show_vars. must come before cats.nodes import

from copy import deepcopy

from munge.proc.filter import Filter
from munge.cats.headed.nodes import Head
from munge.cats.headed.parse import parse_category
from munge.cats.trace import analyse
from munge.trees.traverse import leaves, pairs_postorder, nodes, nodes_postorder
from munge.util.iter_utils import flatten, seqify
from munge.util.err_utils import debug, warn
from munge.util.func_utils import identity
from munge.util.iter_utils import each_pair
from munge.trees.pprint import pprint
from munge.cats.labels import label_result, _label_result
from munge.cats.paths import category_path_to_root, path_to_root
from munge.cats.trace import analyse

from apps.cn.mkmarked import naive_label_derivation, is_modifier
from apps.util.mkdeps_utils import *

unanalysed = set()
def mkdeps(root, postprocessor=strip_index):
    for i, leaf in enumerate(leaves(root)):
        leaf.lex += "*%d" % i
        leaf.cat.parg_labelled()
        leaf.cat.slot.head.lex = leaf.lex
    
    for (l, r, p) in pairs_postorder(root):
        _label_result(l, r, p)
            
    global unanalysed

    for l, r, p in pairs_postorder(root):
        L, R, P = map(lambda x: x and x.cat, (l, r, p))
        comb = analyse(L, R, P)
        if not comb: debug("Unrecognised rule %s %s -> %s", L, R, P)
        
        unifier = []
        
        if config.debug:
            debug("%s %s %s (%s)", L, R, P, str(comb))

        if comb == 'fwd_appl': # [Xx/Yy]l Yy -> Xx
            unifier = unify(L.right, R, head=L)
            p.cat = L.left

        elif comb == 'bwd_appl': # Yy [Xx\Yy]r -> Xx
            unifier = unify(L, R.right, head=R)
            p.cat = R.left
                
        # Pro-drops which drop their outer argument
        # [(S_\NPy)_/NPx]_ -> [S_\NPy]_
        elif comb in ('object_prodrop', 'vp_vp_object_prodrop', 
            'yi_subject_prodrop', 'vp_modifier_subject_prodrop'):
            p.cat = L.left

        # [Xx/Yy]l [Yy/Zz]r -> [Xx/Zz]r
        elif comb == 'fwd_comp': # X/Y Y/Z -> X/Z
            P.slot = R.slot # lexical head comes from R (Y/Z)

            unifier = unify(L.right, R.left, head=R)
            p.cat._left = L.left
            p.cat._right = R.right
            
        # [Yy\Zz]l [Xx\Yy]r -> [Xx\Zz]l
        elif comb == 'bwd_comp': # Y\Z X\Y -> X\Z
            P.slot = L.slot # lexical head comes from L (Y\Z)
            
            unifier = unify(R.right, L.left, head=L)
            p.cat._left = R.left
            p.cat._right = L.right

        elif comb == 'conjoin': # X X[conj] -> X
            copy_vars(frm=R, to=P)

            P.slot = deepcopy(P.slot)
            update_with_fresh_var(p, P.slot)
            P.slot.head.lex = list(flatten((L.slot.head.lex, R.slot.head.lex)))
            
            unifier = unify(L, R, ignore=True, copy_vars=False) # unify variables only in the two conjuncts
            for (dest, src) in unifier:
                old_head = src.slot.head
                
                # look under L and transform all references to 'Z' to references to the 'Z' inside R
                for node in nodes(l):
                    for subcat in node.cat.nested_compound_categories():
                        if subcat.slot.head is old_head:
                            subcat.slot.head = dest.slot.head

            unify(P, R, ignore=True) # unify variables only in the two conjuncts

        elif comb in ('conj_absorb', 'conj_comma_absorb', 'funny_conj'): # conj X -> X[conj]
            copy_vars(frm=R, to=P)
            unify(P, R) # R.slot.head = P.slot.head
        
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
            
        elif comb == 'fwd_xcomp': # [Xx/Yy]l [Yy\Zz]r -> [Xx/Zz]r
            P.slot = R.slot
            
            unifier = unify(L.right, R.left, head=R)
            p.cat._left = L.left
            p.cat._right = R.right

        elif comb == 'bwd_xcomp': # [Yy/Zz]l [Xx\Yy]r -> [Xx/Zz]l
            P.slot = L.slot
            
            unifier = unify(L.left, R.right, head=L)
            p.cat._left = R.left
            p.cat._right = L.right
            
        elif comb == 'bwd_r1xcomp': # [(Yy/Zz)k/Ww]l [Xx\Yy]r -> [(Xx\Zz)k/Ww]l
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
            
        # [NP/NP]y -> NPy
        elif comb == 'de_nominalisation':
            P.slot = L.slot
            
        # {M, QP}y -> (Nf/Nf)y
        elif comb == 'measure_word_number_elision':
            P.slot = L.slot
            
            P.left.slot.var = fresh_var()
            P.right.slot = P.left.slot
            
        elif comb == 'l_punct_absorb':
            p.cat = R
            
        elif comb == 'r_punct_absorb':
            p.cat = L

        elif R and L == R: # VCD (stopgap)
            unify(P, R, head=R) # assume VCD is right headed
            p.cat = R

        else:
            debug('Unhandled combinator %s (%s %s -> %s)', comb, L, R, P)
            unanalysed.add(comb)
            
            P.slot = L.slot
            
        # Fake bidirectional unification:
        # -------------------------------
        # If variable X has been unified with value v,
        # rewrite all mentions of v in the output category to point to variable X
        for (dest, src) in unifier:
            if not isinstance(src, basestring): continue
            
            for subcat in p.cat.nested_compound_categories():
                if subcat.slot.head.lex == src:
                    subcat.slot = dest.slot
            
        if config.debug:
            debug("> %s" % p.cat)
            debug('---')
            
            if config.fail_on_unassigned_variables:
                assert no_unassigned_variables(p.cat), "Unassigned variables in %s" % p.cat
                
    # Collect deps from arguments
    deps = []
    for l in leaves(root):
        if config.debug: debug("%s %s", l.lex, l.cat)
        C = l.cat
        while not C.is_leaf():
            arg = C.right
            if arg.slot.head.filler:
#                print "%s %s %s %s %s %s" % (C.slot.head.lex, C, arg.slot.head.lex, arg, l.cat, C.label)
                deps.append( (C.slot.head.lex, arg.slot.head.lex, l.cat, C.label) )
            C = C.left

    # Produce dep pairs
    result = set()
    for depl, depr, head_cat, head_label in deps:
        for sdepl in set(seqify(depl)):
            for sdepr in set(seqify(depr)):
                if not (sdepl and sdepr):
                    warn("Dependency with None: %s %s", sdepl, sdepr)
                    continue
                    
                result.add( (postprocessor(sdepl), postprocessor(sdepr), head_cat, head_label) )
                
    return result
    
class MakeDependencies(Filter):
    def __init__(self, outdir):
        Filter.__init__(self)
        self.outdir = outdir

    def accept_derivation(self, bundle):
        deps = mkdeps(naive_label_derivation(bundle.derivation), postprocessor=identity)
        self.write_deps(bundle, deps)

    def output(self):
        pass
        
    @staticmethod
    def split_indexed_lex(s):
        return s.split('*')

    def write_deps(self, bundle, deps):
        print '<s id="%s"> %d' % (bundle.label(), len(list(leaves(bundle.derivation))))
        for l, r, head_cat, head_label in deps:
            l, li = self.split_indexed_lex(l)
            r, ri = self.split_indexed_lex(r)
            print ("%-15s " * 6) % tuple(map(str, [li, ri, head_cat, head_label, l, r]))
        print '<\s>'

    opt = '9'
    long_opt = 'mkdeps'

    arg_names = 'OUTDIR'

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError: pass
    
    from munge.ccg.parse import *

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
