from itertools import *

from munge.lex.lex import preserving_split
from munge.cats.nodes import BACKWARD, FORWARD, AtomicCategory, ComplexCategory, ALL
from munge.util.parse_utils import *
from munge.util.exceptions import CatParseException

DefaultMode = ALL

def parse_category(cat_string):
    # Return each mode symbol as a token too when encountered.
    # Important: avoid using mode symbols in atomic category labels.
    toks = preserving_split(cat_string, "(\\/)[]" + ComplexCategory.mode_symbols)

    result = parse_compound(toks)
    ensure_stream_exhausted(toks, 'cats.parse_category')

    return result

def parse_atom(toks):
    atom = toks.next()

    features = []
    while toks.peek() == '[':
        feature = parse_feature(toks)
        features.append(feature)

    return AtomicCategory(atom, features)

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
    
def parse_compound_rhs(toks):
    '''Parses and returns the slash, mode and right hand side of a compound category.'''
    dir = parse_direction(toks)
    mode = None
    if toks.peek() in ComplexCategory.mode_symbols:
        mode = ComplexCategory.mode_symbols.find(toks.next())
        
    right = parse_compound(toks)
    
    return dir, mode, right

def parse_compound(toks):
    '''Parses a compound category.'''
    # Left hand side is a compound category
    if toks.peek() == '(':
        toks.next()

        left = parse_compound(toks)
        shift_and_check( ')', toks )

        if toks.peek() == '[':
            lfeat = parse_feature(toks)
            left.features.append(lfeat)

        if is_direction(toks.peek()):
            dir, mode, right = parse_compound_rhs(toks)
            return ComplexCategory(left, dir, right, DefaultMode if (mode is None) else mode)

        else: return left

    # Left hand side is an atomic category
    else:
        left = parse_atom(toks)

        if is_direction(toks.peek()):
            dir, mode, right = parse_compound_rhs(toks)
            return ComplexCategory(left, dir, right, DefaultMode if (mode is None) else mode)

        else: return left
