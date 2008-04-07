from munge.lex.lex import preserving_split
from munge.cats.repr import BACKWARD, FORWARD, AtomicCategory, CompoundCategory
from munge.util.parse_utils import *
from munge.util.exceptions import CatParseException

def parse_category(cat_string):
    toks = preserving_split(cat_string, "(\\/)[]")

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
    return with_squares(toks.next)

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
            # TODO: add mode recognition here

            if toks.peek() == '(':
                toks.next()

                right = parse_compound(toks)
                shift_and_check( ')', toks )

                if toks.peek() == '[':
                    rfeat = parse_feature(toks)
                    right.features.append(rfeat)

            else:
                right = parse_atom(toks)

            return CompoundCategory(left, dir, right, None) # TODO: add mode recognition here

        else: return left

    else:
        left = parse_atom(toks)

        if is_direction(toks.peek()):
            dir = parse_direction(toks)
            # TODO: add mode recognition here

            if toks.peek() == '(':
                toks.next()

                right = parse_compound(toks)
                shift_and_check( ')', toks )

                if toks.peek() == '[':
                    rfeat = parse_feature(toks)
                    right.features.append(rfeat)

            else:
                right = parse_atom(toks)

            return CompoundCategory(left, dir, right, None)

        else: return left
