from munge.util.exceptions import DocParseException
from itertools import islice

# Inspired by Parsec's _parens_ parser combinator.
# If _func_ recognises the set of strings S, then _with_parens_
# recognises { ( s ) | s \in S }.
def with_parens(func, toks):
    return with_paired_delimiters(func, toks, '()')

def with_angles(func, toks):
    return with_paired_delimiters(func, toks, '<>')

def with_squares(func, toks):
    return with_paired_delimiters(func, toks, '[]')

def with_braces(func, toks):
    return with_paired_delimiters(func, toks, '{}')

def with_paired_delimiters(func, toks, pair):
    shift_and_check( pair[0], toks )
    value = func(toks)
    shift_and_check( pair[1], toks )
    return value

def get_context(toks, ntokens=10):
    return ", ".join(islice(toks, 0, ntokens))


def shift_and_check(tok, toks):
    next = toks.next()
    if tok != next: 
        context = get_context(toks)
        raise DocParseException("Expected %s, got %s {next tokens: %s}" % (tok, next, context))

