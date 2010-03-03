from itertools import izip, islice, tee, takewhile, count, imap
from copy import copy

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

def take(seq, n):
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
    yield e
