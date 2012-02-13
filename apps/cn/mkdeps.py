# coding=utf-8
import sys
from munge.util.config import config
#config.set(show_vars=True, debug=True) # override show_vars. must come before cats.nodes import

from itertools import chain
import traceback

from munge.proc.filter import Filter
from munge.cats.headed.parse import parse_category
from munge.cats.trace import analyse
from munge.trees.traverse import leaves, pairs_postorder
from munge.util.iter_utils import flatten, seqify
from munge.util.err_utils import debug, warn, err
from munge.util.func_utils import identity
from munge.trees.pprint import pprint
from munge.cats.labels import label_result, _label_result
from munge.cats.trace import analyse
from apps.cn.output import OutputDerivation

from apps.cn.mkmarked import naive_label_derivation, is_modifier
from apps.util.mkdeps_utils import *
from apps.cn.fix_rc import is_rooted_in

if config.use_bare_N:
    _NfN = parse_category('N/N')
    _NfNfNfN = parse_category('(N/N)/(N/N)')
else:
    _NfN = parse_category('NP/NP')
    _NfNfNfN = parse_category('(NP/NP)/(NP/NP)')

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
    
def make_set_head_from(l, r, p):
    L, R, P = l.cat, r.cat, p.cat
    
    for ll,rr,pp in zip(L.nested_compound_categories(),R.nested_compound_categories(),P.nested_compound_categories()):
        if ll.slot.head.lex and rr.slot.head.lex:
            pp.slot.head.lex = list(flatten((ll.slot.head.lex, rr.slot.head.lex)))
        else:
            unify(ll,rr,copy_vars=True,ignore=True)
            unify(rr,pp,ignore=True)
            copy_vars(rr,pp)
            
unanalysed = set()
Sdcl = parse_category('S[dcl]')

IndexSeparator = '`'
IndexSeparatorTemplate = IndexSeparator + '%d'
def mkdeps(root, postprocessor=identity):
    for i, leaf in enumerate(leaves(root)):
        # Uniquify each leaf with an index
        leaf.lex += IndexSeparatorTemplate % i
        # Apply the left to right slash labelling 
        # (we abuse this to refer to slots, not slashes)
        leaf.cat.parg_labelled()
        # Populate the outermost (_) variable of each leaf
        leaf.cat.slot.head.lex = leaf.lex

    for (l, r, p) in pairs_postorder(root):
        _label_result(l, r, p)
            
    global unanalysed
    
    unaries = []

    for l, r, p in pairs_postorder(root):
        L, R, P = map(lambda x: x and x.cat, (l, r, p))
        comb = analyse(L, R, P)
        if not comb: debug("Unrecognised rule %s %s -> %s", L, R, P)
        
        unifier = []
        
        if config.debug:
            debug("%s %s %s (%s)", L, R, P, str(comb))

        if comb == 'fwd_appl': # [Xx/Yy]l Yy -> Xx
            unifier = unify(L.right, R)
            p.cat = L.left

        elif comb == 'bwd_appl': # Yy [Xx\Yy]r -> Xx
            unifier = unify(L, R.right)
            p.cat = R.left
                
        # Pro-drops which drop their outer argument
        # [(S_\NPy)_/NPx]_ -> [S_\NPy]_
        elif comb in ('object_prodrop', 'vp_vp_object_prodrop', 
            'yi_subject_prodrop', 'vp_modifier_subject_prodrop'):
            p.cat = L.left

        # [Xx/Yy]l [Yy/Zz]r -> [Xx/Zz]r
        elif comb == 'fwd_comp': # X/Y Y/Z -> X/Z
            if is_rooted_in(Sdcl, L, respecting_features=True):
                P.slot = L.slot
            else:
                P.slot = R.slot # lexical head comes from R (Y/Z)

            P.slot.var = fresh_var(prefix='K')

            unifier = unify(L.right, R.left)
            p.cat._left = L.left
            p.cat._right = R.right
            
        # [Yy\Zz]l [Xx\Yy]r -> [Xx\Zz]l
        elif comb == 'bwd_comp': # Y\Z X\Y -> X\Z
            if is_rooted_in(Sdcl, R, respecting_features=True):
                P.slot = R.slot
            else:
                P.slot = L.slot # lexical head comes from L (Y\Z)

            P.slot.var = fresh_var(prefix='K')
            
            unifier = unify(R.right, L.left)
            p.cat._left = R.left
            p.cat._right = L.right
            
        elif comb in ('s_np_apposition', 'vp_np_apposition'): # { S[dcl], S[dcl]\NP } NPy -> NPy
            P.slot = R.slot # = copy_vars
            unifier = unify(P, R)
            
        # NP NP -> N/N
        elif comb == 'np_np_to_nfn_apposition':
            # do the same as NP NP -> NP, except fill in the vars Ny/Ny
            P.right.slot.var = fresh_var(prefix='N')
            P.left.slot = P.right.slot

            register_unary(unaries, p, L.slot.head.lex)
            make_set_head_from(l, r, p)

        elif comb in ('conjoin', 'np_np_apposition'): # X X[conj] -> X
            make_set_head_from(l, r, p)

        elif comb in ('conj_absorb', 'conj_comma_absorb'): # conj X -> X[conj]
            copy_vars(frm=R, to=P)
            unify(P, R) # R.slot.head = P.slot.head
            
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
            if is_rooted_in(Sdcl, L, respecting_features=True):
                P.slot = L.slot
            else:
                P.slot = R.slot # lexical head comes from R (Y/Z)
                
            P.slot.var = fresh_var(prefix='K')
            
            unifier = unify(L.right, R.left)
            p.cat._left = L.left
            p.cat._right = R.right

        elif comb == 'bwd_xcomp': # [Yy/Zz]l [Xx\Yy]r -> [Xx/Zz]l
            if is_rooted_in(Sdcl, R, respecting_features=True):
                P.slot = R.slot
            else:
                P.slot = L.slot # lexical head comes from L (Y\Z)
        
            # P.slot = L.slot
            P.slot.var = fresh_var(prefix='K')
            
            unifier = unify(R.right, L.left)
            p.cat._left = R.left
            p.cat._right = L.right
            
        elif comb == 'bwd_r1xcomp': # [(Yy/Zz)k/Ww]l [Xx\Yy]r -> [(Xx\Zz)k/Ww]l
            # TODO: where should P's lexical head come from? L or R?
            
            unifier = unify(L.left.left, R.right)
            p.cat._left._left = R.left
            p.cat._left._right = L.left.right
            p.cat._right = L.right

        elif comb in ('fwd_raise', 'bwd_raise'): # Xx -> [ Tf|(Tf|Xx)f ]f
            if P == parse_category(r'(S[dcl]\NP)\((S[dcl]\NP)/(S[dcl]\NP))'):
                # (S[dcl]y\NPz)y -> [ (S[dcl]f\NPg)f/((S[dcl]f\NPg)f\(S[dcl]y\NPz)y)f ]f
                P.left.slot.var = P.left.left.slot.var = P.right.slot.var = P.slot.var = fresh_var() # f 
                P.left.right.slot.var = fresh_var() # g
                
                copy_vars(frm=P.left, to=P.right.left)
                copy_vars(frm=L,      to=P.right.right)
                
                unifier = unify(L, P.right.right)
            elif P == parse_category(r'((S[dcl]\NP)/QP)\(((S[dcl]\NP)/QP)/NP)'):
                # NPy -> [ ((S[dcl]v\NPw)v/QPz)v \ ( ((S[dcl]v\NPw)v/QPz)v/NPy )v ]v
                P.slot.var = fresh_var()
                P.left.slot = P.right.slot = \
                    P.left. left.slot = P.left. left.left.slot = \
                    P.right.left.slot = P.right.left.left.slot = \
                    P.right.left.left.left.slot = P.slot # v
#                P.right.right.slot = fresh_var() # y
                P.right.right.slot = L.slot
                P.left.right.slot.var = fresh_var('Z')
                P.right.left.right.slot = P.left.right.slot # z
                P.left.left.right.slot.var = fresh_var('W')
                P.right.left.left.right.slot = P.left.left.right.slot # w
                
                unifier = unify(L, P.right.right)
            elif P == parse_category(r'(S[dcl]\NP)\((S[dcl]\NP)/QP)'):
                # QPy -> [ (S[dcl]v\NPz)v \ ((S[dcl]v\NPz)v/QPy)v ]v
                P.slot.var = fresh_var()
                P.left.slot = P.left.left.slot = \
                    P.right.slot = P.right.left.slot = P.right.left.left.slot = P.slot # v
#                P.right.right.slot = fresh_var() # y
                P.right.right.slot = L.slot
                P.left.right.slot.var = fresh_var('Z')
                P.right.left.right.slot = P.left.right.slot # z
                
                unifier = unify(L, P.right.right)
            else:
                P.slot.var = fresh_var()

                P.right.left.slot = P.left.slot = P.right.slot = P.slot
                P.right.right.slot = L.slot

                unifier = unify(L, P.right.right)

        elif comb == 'np_typechange':
            P.slot = L.slot # = copy_vars
            unifier = unify(P, L)
            
        elif comb == 'lcp_np_typechange':
            P.slot = L.slot
            unifier = unify(P, L)
            
        elif comb in ('lcp_sfs_typechange', 'lcp_nfn_typechange'):
            P.left.slot.var = fresh_var()
            P.right.slot = P.left.slot
            
            P.slot = L.slot
            
            register_unary(unaries, p, L.slot.head.lex)
            
        elif comb == 'lcp_sbnpfsbnp_typechange':
            # [(Sy\NPz)y/(Sy\NPz)y]_
            P.left.slot.var = fresh_var()
            P.left.left.slot = P.right.left.slot = P.right.slot = P.left.slot
            
            register_unary(unaries, p, L.slot.head.lex)
        
        elif comb == 'null_relativiser_typechange': # Xy -> (Nf/Nf)y
            P.slot = L.slot
            
            if P == _NfN:
                P.left.slot.var = fresh_var()
                
                P.right.slot = P.left.slot
                
                register_unary(unaries, p, L.slot.head.lex)
                
            elif P == _NfNfNfN:
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
            
            register_unary(unaries, p, L.slot.head.lex)
            
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

        elif R and L == R and is_rooted_in(parse_category('S'), L): # VCD (stopgap)
            make_set_head_from(l, r, p)

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
            debug('---')
            
            if config.fail_on_unassigned_variables:
                assert no_unassigned_variables(p.cat), "Unassigned variables in %s" % p.cat
                
    if config.debug:
        debug('unaries: %s', unaries)
        
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
                
    if config.debug:
        for line in write_deps(result):
            debug(line)
    return result

def split_indexed_lex(s):
    return s.split(IndexSeparator)

Template = "%-4s %-4s %-25s %-4s %-15s %s"
def write_parg(bundle, deps):
    bits = ['<s id="%s"> %d' % (bundle.label(), len(list(leaves(bundle.derivation))))]
    bits += write_deps(deps)
    bits.append('<\s>')
    
    return '\n'.join(bits)

def write_deps(deps):
    bits = []
    for l, r, head_cat, head_label in sorted(deps, key=lambda v: int(split_indexed_lex(v[0])[1])):
        l, li = split_indexed_lex(l)
        r, ri = split_indexed_lex(r)
        bits.append(Template % tuple(str(e) for e in (ri, li, head_cat, head_label, r, l)))
    return bits
    
def get_deps(root):
    return mkdeps(naive_label_derivation(root))
    
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
            deps = get_deps(bundle.derivation)
        # Squelch! We need an empty PARG entry even if the process fails, otherwise AUTO and PARG are out of sync
        except Exception, e: 
            err("Processing failed on derivation %s:", bundle.label())
            sys.stderr.flush()
            traceback.print_exc()
            deps = []

        return write_parg(bundle, deps)

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
