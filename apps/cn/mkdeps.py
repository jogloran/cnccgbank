# coding=utf-8
from apps.util.config import config
#config.set(show_vars=True, debug=True) # override show_vars. must come before cats.nodes import

from copy import deepcopy, copy
from itertools import chain
import traceback

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
from apps.cn.output import OutputDerivation

from apps.cn.mkmarked import naive_label_derivation, is_modifier
from apps.util.mkdeps_utils import *

def register_unary(unaries, node, filler):
    '''
    If _node_ represents the result (RHS) of a unary rule, this records that a new
dependency must be created between it and its filler, adding it to _unaries_, a list
of such dependencies created in a given derivation.
    '''
    node.cat.parg_labelled()
    node.cat.slot.head.lex = filler
    debug("%s head lex <- %s", node, filler)
    unaries.append(node)

unanalysed = set()
def mkdeps(root, postprocessor=identity):
    for i, leaf in enumerate(leaves(root)):
        leaf.lex += "*%d" % i
        leaf.cat.parg_labelled()
        leaf.cat.slot.head.lex = leaf.lex

    for (l, r, p) in pairs_postorder(root):
        _label_result(l, r, p)
            
    global unanalysed
    
    unaries = []
    dependers = set()

    for l, r, p in pairs_postorder(root):
        L, R, P = map(lambda x: x and x.cat, (l, r, p))
        comb = analyse(L, R, P)
        if not comb: debug("Unrecognised rule %s %s -> %s", L, R, P)
        
        unifier = []
        
        if config.debug:
            debug("%s %s %s (%s)", L, R, P, str(comb))
            debug("dependers: %s", dependers)

        if comb == 'fwd_appl': # [Xx/Yy]l Yy -> Xx
            unifier = unify(L.right, R, dependers, head=L)
            p.cat = L.left

        elif comb == 'bwd_appl': # Yy [Xx\Yy]r -> Xx
            unifier = unify(L, R.right, dependers, head=R)
            p.cat = R.left
                
        # Pro-drops which drop their outer argument
        # [(S_\NPy)_/NPx]_ -> [S_\NPy]_
        elif comb in ('object_prodrop', 'vp_vp_object_prodrop', 
            'yi_subject_prodrop', 'vp_modifier_subject_prodrop'):
            p.cat = L.left

        # [Xx/Yy]l [Yy/Zz]r -> [Xx/Zz]r
        elif comb == 'fwd_comp': # X/Y Y/Z -> X/Z
            P.slot = R.slot # lexical head comes from R (Y/Z)
            P.slot.var = fresh_var(prefix='K')

            unifier = unify(L.right, R.left, dependers, head=R)
            p.cat._left = L.left
            p.cat._right = R.right
            
        # [Yy\Zz]l [Xx\Yy]r -> [Xx\Zz]l
        elif comb == 'bwd_comp': # Y\Z X\Y -> X\Z
            P.slot = L.slot # lexical head comes from L (Y\Z)
            P.slot.var = fresh_var(prefix='K')
            
            unifier = unify(R.right, L.left, dependers, head=L)
            p.cat._left = R.left
            p.cat._right = L.right
            
        elif comb in ('s_np_apposition', 'vp_np_apposition'): # { S[dcl], S[dcl]\NP } NPy -> NPy
            P.slot = R.slot # = copy_vars
            unifier = unify(P, R, dependers)

        elif comb == 'conjoin': # X X[conj] -> X
            copy_vars(frm=R, to=P)

            P.slot = deepcopy(P.slot)
            update_with_fresh_var(p, P.slot)
            P.slot.head.lex = list(flatten((L.slot.head.lex, R.slot.head.lex)))
            
            unifier = unify(L, R, dependers, ignore=True, copy_vars=False) # unify variables only in the two conjuncts
            for (dest, src) in unifier:
                if isinstance(src, (basestring, list)): continue
                
                old_head = src.slot.head
                
                # look under L and transform all references to 'Z' to references to the 'Z' inside R
                for node in nodes(l):
                    for subcat in node.cat.nested_compound_categories():
                        if subcat.slot.head is old_head:
                            subcat.slot.head = dest.slot.head

            unify(P, R, dependers, ignore=True) # unify variables only in the two conjuncts

        elif comb in ('conj_absorb', 'conj_comma_absorb'): # conj X -> X[conj]
            copy_vars(frm=R, to=P)
            unify(P, R, dependers) # R.slot.head = P.slot.head
            
        elif comb == 'funny_conj': # conj X -> X
            p.cat = R
        
        elif comb == 'nongap_topicalisation': # {N, NP, S[dcl], QP}x -> [Sy/Sy]x
            P.slot = L.slot
            P.right.slot.var = fresh_var()
            P.left.slot = P.right.slot
            
            register_unary(unaries, p, L.slot.head.lex)
            
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
            P.slot.var = fresh_var(prefix='K')
            
            unifier = unify(L.right, R.left, dependers, head=R)
            p.cat._left = L.left
            p.cat._right = R.right

        elif comb == 'bwd_xcomp': # [Yy/Zz]l [Xx\Yy]r -> [Xx/Zz]l
            P.slot = L.slot
            P.slot.var = fresh_var(prefix='K')
            
            unifier = unify(L.left, R.right, dependers, head=L)
            p.cat._left = R.left
            p.cat._right = L.right
            
        elif comb == 'bwd_r1xcomp': # [(Yy/Zz)k/Ww]l [Xx\Yy]r -> [(Xx\Zz)k/Ww]l
            # TODO: where should P's lexical head come from? L or R?
            
            unifier = unify(L.left.left, R.right, dependers)
            p.cat._left._left = R.left
            p.cat._left._right = L.left.right
            p.cat._right = L.right

        elif comb in ('fwd_raise', 'bwd_raise'): # Xx -> [ Tf|(Tf|Xx)f ]f
            P.slot.var = fresh_var()

            P.right.left.slot = P.left.slot = P.right.slot = P.slot
            P.right.right.slot = L.slot

            unifier = unify(L, P.right.right, dependers)

        elif comb == 'np_typechange':
            P.slot = L.slot # = copy_vars
            unifier = unify(P, L, dependers)
        
        elif comb == 'null_relativiser_typechange': # Xy -> (Nf/Nf)y
            P.slot = L.slot
            
            if P == parse_category(r'N/N'):
                P.left.slot.var = fresh_var()
                
                P.right.slot = P.left.slot
                
                if L.slot.head.lex is None:
                    debug("P: %s, L: %s", P, L)
                register_unary(unaries, p, L.slot.head.lex)
                
            elif P == parse_category(r'(N/N)/(N/N)'):
                P.left.slot.var = fresh_var()
                P.left.left.slot.var = fresh_var(prefix="G")
                
                P.left.right.slot = P.left.left.slot
                P.right.slot = P.left.slot
                
                register_unary(unaries, p, L.slot.head.lex)
            else:
                warn("Unhandled null relativiser typechange: %s -> %s", L, P)
            
        # [NP/NP]y -> NPy
        elif comb == 'de_nominalisation':
            P.slot = L.slot
            
        # {M, QP}y -> (Nf/Nf)y
        elif comb == 'measure_word_number_elision':
            P.slot = L.slot
            
            P.left.slot.var = fresh_var()
            P.right.slot = P.left.slot
            
            register_unary(unaries, p, L.slot.head.lex)
            
        elif comb == 'l_punct_absorb': # , X -> X[conj]
            # need to put conj feature back on parent
            p.cat = R.clone_adding_feature('conj')
            
        elif comb == 'r_punct_absorb':
            p.cat = L

        elif R and L == R: # VCD (stopgap)
            unify(P, R, dependers, head=R) # assume VCD is right headed
            p.cat = R

        else:
            debug('Unhandled combinator %s (%s %s -> %s)', comb, L, R, P)
            unanalysed.add(comb)
            
            P.slot = R.slot if R else L.slot
            
        for (dest, src) in unifier:
            if isinstance(src, (basestring, list)):
                # Fake bidirectional unification:
                # -------------------------------
                # If variable X has been unified with value v,
                # rewrite all mentions of v in the output category to point to variable X
                # (v is uniquified by concatenating it with an ID, so this should hold)            
                for subcat in p.cat.nested_compound_categories():
                    if subcat.slot.head.lex == src:
                        subcat.slot = dest.slot
            
        if config.debug:
            debug("> %s" % p.cat)
            debug("> dependers: %s", dependers)
            debug('---')
            
            if config.fail_on_unassigned_variables:
                assert no_unassigned_variables(p.cat), "Unassigned variables in %s" % p.cat
                
    # Collect deps from arguments
    deps = []
    for l in chain( leaves(root), unaries ):
        if config.debug: debug("%s %s", l, l.cat)
        
        C = l.cat
        while not C.is_leaf():
            arg = C.right
            if arg.slot.head.filler:
                #and not l.cat.left.slot == l.cat.right.slot):
        #        print "%s %s %s %s %s %s" % (C.slot.head.lex, C, arg.slot.head.lex, arg, l.cat, C.label)
                if C.label is None:
                    warn("Dependency generated on slash without label: %s %s", C, arg)
                deps.append( (C.slot.head.lex, arg.slot.head.lex, l.cat, C.label) )
            if is_modifier(C): break
            C = C.left

    # Produce dep pairs
    result = set()
    for depl, depr, head_cat, head_label in deps:
        for sdepl in set(seqify(depl)):
            for sdepr in set(seqify(depr)):
                if not (sdepl and sdepr):
                    debug("Dependency with None: %s %s", sdepl, sdepr)
                    continue
                    
                result.add( (postprocessor(sdepl), postprocessor(sdepr), head_cat, head_label) )
                
    return result

def split_indexed_lex(s):
    return s.split('*')

Template = "%-4s %-4s %-25s %-4s %-15s %s"
def write_deps(bundle, deps):
    bits = ['<s id="%s"> %d' % (bundle.label(), len(list(leaves(bundle.derivation))))]
    for l, r, head_cat, head_label in sorted(deps, key=lambda v: int(split_indexed_lex(v[0])[1])):
        l, li = split_indexed_lex(l)
        r, ri = split_indexed_lex(r)
        bits.append(Template % tuple(str(e) for e in (ri, li, head_cat, head_label, r, l)))
    bits.append('<\s>')
    
    return '\n'.join(bits)
    
class MakeDependencies(Filter, OutputDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputDerivation.__init__(self, outdir, transformer=self.process, 
            fn_template=lambda bundle: "chtb_%02d%02d.parg" % (bundle.sec_no, bundle.doc_no),
            outdir_template=lambda outdir, bundle: "%s/%02d" % (outdir, bundle.sec_no))
        
    def accept_derivation(self, bundle):
        self.write_derivation(bundle)

    @staticmethod
    def process(bundle):
        try:
            deps = mkdeps(naive_label_derivation(bundle.derivation), postprocessor=identity)
        # Squelch! We need an empty PARG entry even if the process fails, otherwise AUTO and PARG are out of sync
        except Exception, e: 
            traceback.print_exc()
            deps = []

        return write_deps(bundle, deps)

    opt = '9'
    long_opt = 'mkdeps'

    arg_names = 'OUTDIR'

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError: pass
    
    from munge.ccg.parse import *

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
