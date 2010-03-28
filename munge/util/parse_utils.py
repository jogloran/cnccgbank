from munge.util.exceptions import DocParseException
from munge.util.iter_utils import take
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
    assert len(pair) == 2
    
    shift_and_check( pair[0], toks )
    value = func(toks)
    shift_and_check( pair[1], toks )
    return value

def get_context(toks, ntokens=10):
    return ", ".join(take(toks, ntokens))

def shift_and_check(tok, toks):
    '''Peeks at a lexer token from the stream _toks_, throwing a DocParseException unless
the token matches _tok_.'''
    next = toks.next()
    if tok != next: 
        context = get_context(toks)
        raise DocParseException("Expected %s, got %s {next tokens: %s}" % (tok, next, context))

DefaultContextLength = 10
def ensure_stream_exhausted(toks, caller, context_length=DefaultContextLength):
    '''Raises a DocParseException unless the stream _toks_ is empty. If not empty, displays
a preview of the first few remaining tokens in the stream.'''
    if toks.peek() is not None:
        raise DocParseException, "%s: Tokens at end of input. {next tokens: %s}" % (caller, list(take(toks, context_length)))
