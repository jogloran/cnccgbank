import sys, copy

from munge.cats.headed.parse import *
from munge.cats.cat_defs import S, Sdcl, NP, N
from munge.util.err_utils import *
from munge.trees.traverse import leaves

from apps.util.echo import echo

def variables():
    return iter('_YZWVUTRQABCDEF')

def is_modifier(cat):
    return cat.left == cat.right

def is_np_n(cat):
    return cat.left == NP and cat.right == N
    
C = parse_category
Exceptions = (
    (C(r'(N/N)\(S[dcl]\NP)'), C(r'((N{Z}/N{Z}){_}\(S[dcl]{Y}\NP{Z}){Y}){_}')),
    (C(r'(N/N)\(S[dcl]/NP)'), C(r'((N{Z}/N{Z}){_}\(S[dcl]{Y}/NP{Z}){Y}){_}')),
    (C(r'(S[dcl]\NP)/(S[dcl]\NP)'), C(r'((S[dcl]{_}\NP{Y}){_}/(S[dcl]{Z}\NP{Y}){Z}){_}'))
)

def get_cached_category_for(cat, lex):
    for frm, to in Exceptions:
        if cat.equal_respecting_features(frm):
            result = copy.deepcopy(to)
            result.slot.head.lex = lex
            return result
    return None

n = 1
def label(cat, vars=None, lex=None):
    global n
    cached = get_cached_category_for(cat, lex)
    if cached: 
        cp = copy.deepcopy(cached)
        cp.slot.head.lex = cat.slot.head.lex
        return cp
        
    available = vars or variables()

    if cat.slot.var == "?":
        cat.slot.var = (available.next() + str(n))

    if cat.is_complex():
        c = cat
        while c.is_complex() and not (is_modifier(c) or is_np_n(c)):
            c.left.slot = cat.slot
            c = c.left

        if is_modifier(cat):
            cat._left = label(cat.left, available)
            cat._right = cat._left

        elif is_np_n(cat):
            cat._left = label(cat.left, available)
            cat._right.slot.var = cat._left.slot.var

        else:
            cat._left = label(cat.left, available)
            cat._right = label(cat.right, available)

    n += 1
    return cat

def write_markedup(cats, file):
    for cat in cats:
        print >>file, cat.__repr__(suppress_vars=True)
        print >>file, "\t", 0, cat.__repr__()
        print >>file

def naive_label_derivation(root):
    for leaf in leaves(root):
#        print "%s ->" % leaf.cat,
        leaf.cat = label(leaf.cat, lex=leaf.lex)
#        print "%s" % leaf.cat
        
    return root

if __name__ == '__main__':
    # for cat in cats:
    #     print label(cat)

    #import sys
    #write_markedup(map(label, cats), sys.stdout)

    print label(parse_category(r'((S\NP)/(S\NP))/NP'))
    print label(parse_category(r'(S\NP)/(S\NP)'))
    print label(parse_category(r'(S[dcl]\NP)/NP'))
    print label(parse_category(r'((S[dcl]\NP)/NP)/PP'))
    print label(parse_category(r'(((S[dcl]\NP)/NP)/NP)/PP'))
    print label(parse_category(r'(S[dcl]\NP)/(S[dcl]\NP)'))
    print label(parse_category(r'N/N'))
    print label(parse_category(r'(N/N)/(N/N)'))
    print label(parse_category(r'((N/N)/(N/N))/((N/N)/(N/N))'))
    print label(parse_category(r'PP/LCP'))
    print label(parse_category(r'NP'))
    print label(parse_category(r'(N/N)\NP'))
    print label(parse_category(r'(NP\NP)/(S[dcl]\NP)'))
    print label(parse_category(r'NP/N'))
    print label(parse_category(r'(N/N)\(S[dcl]/NP)'))
