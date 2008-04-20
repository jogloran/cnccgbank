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
    if toks.peek() is not None:
        raise CatParseException, "Tokens at end of input while parsing category %s." % cat_string

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

def parse_compound(toks):
    if toks.peek() == '(':
        toks.next()

        left = parse_compound(toks)
        shift_and_check( ')', toks )

        if toks.peek() == '[':
            lfeat = parse_feature(toks)
            left.features.append(lfeat)

        if is_direction(toks.peek()):
            dir = parse_direction(toks)
            
            # see if a mode symbol is present
            mode = None
            # Derivation 5:95(15) is broken; there is a malformed category ((S[b]\NP)/NP)/
            if toks.peek() in ComplexCategory.mode_symbols:
                mode = ComplexCategory.mode_symbols.find(toks.next())

            if toks.peek() == '(':
                toks.next()

                right = parse_compound(toks)
                shift_and_check( ')', toks )

                if toks.peek() == '[':
                    rfeat = parse_feature(toks)
                    right.features.append(rfeat)

            else:
                right = parse_atom(toks)

            return ComplexCategory(left, dir, right, mode or DefaultMode) # TODO: add mode recognition here

        else: return left

    else: # TODO: this duplicates the above exactly. write this better.
        left = parse_atom(toks)

        if is_direction(toks.peek()):
            dir = parse_direction(toks)

            # see if a mode symbol is present
            mode = None
            if toks.peek() in ComplexCategory.mode_symbols:
                mode = ComplexCategory.mode_symbols.find(toks.next())

            if toks.peek() == '(':
                toks.next()

                right = parse_compound(toks)
                shift_and_check( ')', toks )

                if toks.peek() == '[':
                    rfeat = parse_feature(toks)
                    right.features.append(rfeat)

            else:
                right = parse_atom(toks)

            return ComplexCategory(left, dir, right, mode or DefaultMode)

        else: return left
