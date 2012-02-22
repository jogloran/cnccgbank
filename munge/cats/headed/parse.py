# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from itertools import *

from munge.lex.lex import preserving_split
from munge.cats.nodes import BACKWARD, FORWARD, ALL
from munge.cats.headed.nodes import AtomicCategory, ComplexCategory, Slot
from munge.util.parse_utils import *
from munge.util.exceptions import CatParseException

from munge.util.deco_utils import memoised

DefaultMode = ALL

def parse_alias(toks):
    toks.next() # skip over the '~'
    return toks.next()

# IMPORTANT: memoised is off for headed categories
def parse_category(cat_string):
    # Return each mode symbol as a token too when encountered.
    # Important: avoid using mode symbols in atomic category labels.
    toks = preserving_split(cat_string, "(\\/)[]{}~")# + ComplexCategory.mode_symbols)

    result = parse_compound(toks, {})
    if toks.peek() == '~':
        result.alias = parse_alias(toks)
        
    ensure_stream_exhausted(toks, 'cats.parse_category')

    return result

def parse_atom(toks, vars):
    atom = toks.next()

    features = []
    var = None
    while toks.peek() == '[':
        feature = parse_feature(toks)
        features.append(feature)

    ret = AtomicCategory(atom, features)
        
    if toks.peek() == '{':
        var = parse_var(toks)
        ret.slot = make_var(vars, var)
        
    return ret

def parse_direction(toks):
    slash = toks.next()

    if slash == '/':
        return FORWARD
    elif slash == '\\':
        return BACKWARD
    else:
        raise CatParseException, "Expected a slash direction (\\, /)."

def is_direction(char):
    return char in ('/', '\\')

def parse_feature(toks):
    return with_squares(lambda toks: toks.next(), toks)
    
def parse_var(toks):
    return with_braces(lambda toks: toks.next(), toks)
    
def parse_compound_rhs(toks, vars):
    '''Parses and returns the slash, mode and right hand side of a compound category.'''
    dir = parse_direction(toks)
    mode = None
    if toks.peek() in ComplexCategory.mode_symbols:
        mode = ComplexCategory.mode_symbols.find(toks.next())
        
    right = parse_compound(toks, vars)
    
    return dir, mode, right
    
def make_var(vars, var_name):
    if not vars.get(var_name, None):
        vars[var_name] = Slot(var_name)
    return vars[var_name]

def parse_compound(toks, vars):
    '''Parses a compound category.'''
    # Left hand side is a compound category
    if toks.peek() == '(':
        toks.next()

        left = parse_compound(toks, vars)
        shift_and_check( ')', toks )

        if toks.peek() == '[':
            lfeat = parse_feature(toks)
            left.features.append(lfeat)
            
        if toks.peek() == '{':
            lvar = parse_var(toks)
            left.slot = make_var(vars, lvar)

        if is_direction(toks.peek()):
            dir, mode, right = parse_compound_rhs(toks, vars)
            return ComplexCategory(left, dir, right, DefaultMode if (mode is None) else mode)

        else: return left

    # Left hand side is an atomic category
    else:
        left = parse_atom(toks, vars)

        if is_direction(toks.peek()):
            dir, mode, right = parse_compound_rhs(toks, vars)
            return ComplexCategory(left, dir, right, DefaultMode if (mode is None) else mode)

        else: return left
        
