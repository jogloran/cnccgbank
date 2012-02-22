# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from itertools import izip, islice, tee
from functools import partial as curry

def each_pair(seq):
    '''Given an iterator (i0, i1, i2, ...), returns an iterator ((i0, i1), (i1, i2), ...).'''
    s1, s2 = tee(seq)
    return izip(s1, islice(s2, 1, None))

def flatten(seq):
    '''Recursively flattens a sequence such as (A, (B, C, (D, E))) into a non-nested
sequence (A, B, C, D, E).'''
    for element in iter(seq):
        if isinstance(element, (list, tuple)):
            for subelement in flatten(element):
                yield subelement
        else:
            yield element
            
def reject(orig_seq, pred):
    '''Given a sequence and a predicate, this accepts only elements which do not satisfy the
predicate.'''
    orig_seq, seq = tee(orig_seq, 2)
    
    return (element for element in seq if not pred(element))

def take(n, seq):
    '''Returns the first _n_ elements from the given sequence.'''
    return islice(seq, 0, n)

def seqify(e):
    '''If _e_ is a sequence, returns an iterator over _e_. Otherwise, returns a single-element
iterator yielding _e_.'''
    if isinstance(e, (list, tuple)):
        for el in e: yield el
    else:
        yield e
        
def single(e):
    '''Yields an iterator over a single element _e_.'''
    yield e

get_first = curry(take, 1)

def intersperse(seq, spacer):
    '''Given a sequence _seq_, intersperses the given _spacer_ between each pair of elements.'''
    first = True
    for e in seq:
        if first:
            first = False
        else:
            yield spacer
        yield e