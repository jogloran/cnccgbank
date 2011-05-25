import sys, copy

from apps.util.config import config
config.set(show_vars=True, curly_vars=True)

from munge.cats.headed.parse import *
from munge.cats.cat_defs import S, Sdcl, NP, N
from munge.util.err_utils import *
from munge.trees.traverse import leaves

from apps.util.echo import echo

def variables():
    '''Returns an iterator over variable names. The first variable name returned is _,
for the outermost variable.'''
    return iter('_YZWVUTRQAB')#CDEF')

def is_modifier(cat):
    '''Returns whether _cat_ is of the form X/X.'''
    return cat.left.equal_respecting_features(cat.right) and cat.left.slot.var is cat.right.slot.var

def is_np_n(cat):
    '''Returns whether _cat_ is the category NP/N.'''
    return cat.left == NP and cat.right == N
    
C = parse_category
Exceptions = (
# TODO: trying remapping to avoid conflicts
# Y -> F
# Z -> E
# W -> D
# V -> C
    (C(r'(N/N)\(S[dcl]\NP)'), C(r'((N{E}/N{E}){_}\(S[dcl]{F}\NP{E}){F}){_}')),
    (C(r'(N/N)\(S[dcl]/NP)'), C(r'((N{E}/N{E}){_}\(S[dcl]{F}/NP{E}){F}){_}')),
    (C(r'(S[dcl]\NP)/(S[dcl]\NP)'), C(r'((S[dcl]{_}\NP{F}){_}/(S[dcl]{E}\NP{F}){E}){_}')),
    # gapped long bei
    (C(r'((S[dcl]\NP)/((S[dcl]\NP)/NP))/NP'), C(r'(((S[dcl]{_}\NP{F}){_}/((S[dcl]{E}\NP{D}){E}/NP{F}){E}){_}/NP{D}){_}')),
    # non-gapped long bei
    (C(r'((S[dcl]\NP)/(S[dcl]\NP))/NP'), C(r'(((S[dcl]{_}\NP{D}){_}/(S[dcl]{E}\NP{F}){E}){_}/NP{F}){_}')),
    # gapped short bei
    (C(r'(S[dcl]\NP)/((S[dcl]\NP)/NP)'), C(r'((S[dcl]{_}\NP{F}){_}/((S[dcl]{D}\NP{E}){D}/NP{F}){D}){_}')),
    # non-gapped short bei
    # TODO: coincides with the above control/raising category
#    (C(r'(S[dcl]\NP)/(S[dcl]\NP)'), C(r'((S[dcl]{_}\NP){_}/(S[dcl]\NP)){_}')),

    # hacks
    # not a modifier category:
    (C(r'((S[dcl]\NP)/(S[dcl]\NP))/((S[dcl]\NP)/(S[dcl]\NP))'),
     C(r'(((S[dcl]{F}\NP{E}){F}/(S[dcl]{D}\NP{E}){D}){F}/((S[dcl]{F}\NP{E}){F}/(S[dcl]{D}\NP{E}){D}){F}){_}')),
     
    (C(r'((S[dcl]\NP)/NP)/((S[dcl]\NP)/NP)'),
     C(r'(((S[dcl]{F}\NP{E}){F}/NP{D}){F}/((S[dcl]{F}\NP{E}){F}/NP{D}){F}){_}')),
     
    (C(r'(((S[dcl]\NP)/(S[dcl]\NP))/NP)/(((S[dcl]\NP)/(S[dcl]\NP))/NP)'),
     C(r'((((S[dcl]{F}\NP{E}){F}/(S[dcl]{D}\NP{C}){D}){F}/NP{G}){F}/(((S[dcl]{F}\NP{E}){F}/(S[dcl]{D}\NP{C}){D}){F}/NP{G}){F}){_}')),
     
    #(C(r'((S[dcl]\NP)/((S[dcl]\NP)/NP))/NP'),
    # C(r'(((S[dcl]{_}\NP{F}){_}/((S[dcl]{E}\NP{D}){E}/NP{F}){E}){_}/NP{D}){_}')),
     
    # make sure things which look like modifier categories but aren't are given the right markedup
    # these are all attested categories of the form (S[dcl]\S[dcl])/$
    # TODO: we don't need to do this: just define a mapping for S[dcl]\S[dcl] and anything that uses it should
    #       pick up correct markedup
    (C(r'(S[dcl]\S[dcl])/NP'), C(r'((S[dcl]{_}\S[dcl]{E}){_}/NP{F}){_}')),
    (C(r'(S[dcl]\S[dcl])/(S[dcl]\NP)'), C(r'((S[dcl]{_}\S[dcl]{E}){_}/(S[dcl]{F}\NP{D}){F}){_}')),
    (C(r'(S[dcl]\S[dcl])/S[dcl]'), C(r'((S[dcl]{_}\S[dcl]{E}){_}/S[dcl]{F}){_}')),
    (C(r'(S[dcl]\S[dcl])/PP'), C(r'((S[dcl]{_}\S[dcl]{E}){_}/PP{F}){_}')),
    (C(r'(S[dcl]\S[dcl])/QP'), C(r'((S[dcl]{_}\S[dcl]{E}){_}/QP{F}){_}')),
    (C(r'(S[dcl]\S[dcl])/M'), C(r'((S[dcl]{_}\S[dcl]{E}){_}/M{F}){_}')),
    (C(r'S[dcl]\S[dcl]'), C(r'(S[dcl]{_}\S[dcl]{E}){_}')),
    
    (C(r'(S\S)\(S\S)'), C(r'((S{F}\S{E}){F}\(S{F}\S{E}){F}){_}')),
    (C(r'(S\S)/(S\S)'), C(r'((S{F}\S{E}){F}/(S{F}\S{E}){F}){_}')),
    (C(r'(S\S)/(S\NP)'), C(r'((S{F}\S{E}){F}/(S{F}\NP{D}){F}){_}')),
    (C(r'(S\LCP)/(S\NP)'), C(r'((S{F}\LCP{E}){F}/(S{F}\NP{D}){F}){_}')),
    (C(r'(S\QP)/(S\NP)'), C(r'((S{F}\QP{E}){F}/(S{F}\NP{D}){F}){_}')),
    
    (C(r'((S\S)/(S\NP))/NP'), C(r'(((S{F}\S{E}){F}/(S{D}\NP{C}){D}){_}/NP{F}){_}')),

    (C(r'S[q]\S[dcl]'), C(r'(S[q]{F}\S[dcl]{F}){_}')),

    # short bei for bei VPdcl/VPdcl (wo bei qiangzhi)
    (C(r'(S[dcl]\NP)/(((S[dcl]\NP)/(S[dcl]\NP))/NP)'), C(r'((S[dcl]{_}\NP{F}){_}/(((S[dcl]{E}\NP{F}){E}/(S[dcl]{D}\NP{F}){D}){E}/NP{F}){E}){_}')),

    # long bei for bei NP VPdcl/VPdcl (wo bei ta qiangzhi)
    (C(r'((S[dcl]\NP)/(((S[dcl]\NP)/(S[dcl]\NP))/NP))/NP'),
     C(r'(((S[dcl]{_}\NP{F}){_}/(((S[dcl]{C}\NP{E}){C}/(S[dcl]{D}\NP{F}){D}){C}/NP{F}){C}){_}/NP{E}){_}')),
      #C(r'(((S[dcl]{_}\NP{F}){_}/(((S[dcl]{D}\NP{E}){D}/(S[dcl]{C}\NP{F}){C}){D}/NP{F}){D}){_}/NP{E}){_}')),
    
    # VPdcl/VPdcl modifier category fix
    (C(r'(((S[dcl]\NP)/(S[dcl]\NP))/NP)/(((S[dcl]\NP)/(S[dcl]\NP))/NP)'), 
     C(r'((((S[dcl]{E}\NP{F}){E}/(S[dcl]{D}\NP{F}){D}){E}/NP{F}){C}/(((S[dcl]{E}\NP{F}){E}/(S[dcl]{D}\NP{F}){D}){E}/NP{F}){C}){_}')),
    
    # gei category fix (NP gei NP NP VP e.g. tamen gei haizi jihui xuanze)
    (C(r'(((S[dcl]\NP)/(S[dcl]\NP))/NP)/NP'),
     C(r'((((S[dcl]{_}\NP{D}){_}/(S[dcl]{D}\NP{F}){D}){_}/NP{E}){_}/NP{F}){_}')),

    # this category is probably not correct
    (C(r'((S[dcl]\NP)/(S[dcl]\NP))/S[dcl]'),
     C(r'(((S[dcl]{_}\NP{C}){_}/(S[dcl]{D}\NP{E}){D}){_}/S[dcl]{F}){_}')),
    
    # nor this (20:31(7))
    (C(r'((S[dcl]\NP)/(S[dcl]\NP))/PP'),
     C(r'(((S[dcl]{_}\NP{F}){_}/(S[dcl]{D}\NP{E}){D}){_}/PP{C}){_}')),

)

def get_cached_category_for(cat, lex):
    '''If _cat_ matches one of the mappings defined in Exceptions, returns a copy of
the cached category, filling in its outermost variable's lex with _lex_.'''
    for frm, to in Exceptions:
        if cat.equal_respecting_features(frm):
            result = copy.deepcopy(to)
#            result.slot.head.lex = lex
            return result
    return None

n = 1
def label(cat, vars=None, lex=None):
    '''Labels the category _cat_ using the markedup labelling algorithm, with
available variable labels _vars_ and lexical item _lex_.'''
    global n
    cached = get_cached_category_for(cat, lex)
    if cached: 
        cp = copy.deepcopy(cached)
#        cp.slot.head.lex = cat.slot.head.lex
        return cp
        
    available = vars or variables()

    if cat.slot.var == "?":
        suffix = str(n) if config.debug_vars else ''
        cat.slot.var = (available.next() + suffix)

    if cat.is_complex():
        c = cat
        while c.is_complex() and not (is_modifier(c) or is_np_n(c)):
            c.left.slot = cat.slot
            c = c.left

        if is_modifier(cat):
            cat._left = label(cat.left, available, lex)
            cat._right = copy.copy(cat._left)

        elif is_np_n(cat):
            cat._left = label(cat.left, available, lex)
            cat._right.slot = cat._left.slot

        else:
            cat._left = label(cat.left, available, lex)
            cat._right = label(cat.right, available, lex)

    n += 1
    return cat

PREFACE = "# this file was generated by the following command(s):"
def write_markedup(cats, file):
    print >>file, PREFACE
    print >>file
    
    for cat in cats:
        print >>file, cat.__repr__(suppress_vars=True)
        print >>file, "\t", 0, cat.__repr__()
        print >>file

def naive_label_derivation(root):
    '''Applies the markedup labelling algorithm to each leaf under _root_.'''
    for leaf in leaves(root):
#        print "%s ->" % leaf.cat,
        leaf.cat = label(leaf.cat, lex=leaf.lex)
        leaf.cat.slot.head.lex = leaf.lex
#        print "%s" % leaf.cat
        
    return root

if __name__ == '__main__':
    # for cat in cats:
    #     print label(cat)

    import sys
    write_markedup(map(label, map(parse_category, sys.stdin.xreadlines())), sys.stdout)
    # 
    # print label(parse_category(r'((S\NP)/(S\NP))/NP'))
    # print label(parse_category(r'(S\NP)/(S\NP)'))
    # print label(parse_category(r'(S[dcl]\NP)/NP'))
    # print label(parse_category(r'((S[dcl]\NP)/NP)/PP'))
    # print label(parse_category(r'(((S[dcl]\NP)/NP)/NP)/PP'))
    # print label(parse_category(r'(S[dcl]\NP)/(S[dcl]\NP)'))
    # print label(parse_category(r'N/N'))
    # print label(parse_category(r'(N/N)/(N/N)'))
    # print label(parse_category(r'((N/N)/(N/N))/((N/N)/(N/N))'))
    # print label(parse_category(r'PP/LCP'))
    # print label(parse_category(r'NP'))
    # print label(parse_category(r'(N/N)\NP'))
    # print label(parse_category(r'(NP\NP)/(S[dcl]\NP)'))
    # print label(parse_category(r'NP/N'))
    # print label(parse_category(r'(N/N)\(S[dcl]/NP)'))
