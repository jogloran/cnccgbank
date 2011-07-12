from munge.util.exceptions import DocParseException
from munge.util.iter_utils import take
from functools import partial as curry

def with_paired_delimiters(pair, func, toks):
    shift_and_check( pair[0], toks )
    value = func(toks)
    shift_and_check( pair[1], toks )
    return value

# Inspired by Parsec's _parens_ parser combinator.
# If _func_ recognises the set of strings S, then _with_parens_
# recognises { ( s ) | s \in S }.
with_parens = curry(with_paired_delimiters, '()')
with_angles = curry(with_paired_delimiters, '<>')
with_squares = curry(with_paired_delimiters, '[]')
with_braces = curry(with_paired_delimiters, '{}')

def get_context(toks, ntokens=10):
    return ", ".join(take(ntokens, toks))

def shift_and_check(tok, toks):
    '''Peeks at a lexer token from the stream _toks_, throwing a DocParseException unless
the token matches _tok_.'''
    next = toks.next()
    if tok != next: 
        context = get_context(toks)
        raise DocParseException("Expected %s, got %s {next tokens: %s}" % (tok, next, context))

DefaultContextLength = 20
def ensure_stream_exhausted(toks, caller, context_length=DefaultContextLength):
    '''Raises a DocParseException unless the stream _toks_ is empty. If not empty, displays
a preview of the first few remaining tokens in the stream.'''
    if toks.peek() is not None:
        raise DocParseException, "%s: Tokens at end of input. {next tokens: %s}" % (caller, list(take(context_length, toks)))
