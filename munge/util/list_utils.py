from itertools import izip, count

def first_index_such_that(pred, l):
    '''Finds the first index satisfying the given predicate, or None if no index does.'''
    for e, i in izip(list(l), count()):
        if pred(e): return i
    return None
    
def last_index_such_that(pred, l):
    '''Finds the last index satisfying the given predicate (counted from the end) satisfying
the given predicate, or None if no index does.'''
    return first_index_such_that(pred, reversed(list(l)))
    
def is_sublist(smaller, larger):
    '''Implements naive string matching.'''
    m = len(smaller)
    for start in range(0, (len(larger) - m + 1) + 1):
        if larger[start:(start+m)] == smaller: return True
        
    return False
    
def find(pred, l):
    for e in l:
        if pred(e): return e
        
    return None
    
def starmap(f, l):
    '''Given a sequence ((A1, B1, ...), (A2, B2, ...)) and a function (A, B, ...) -> C, this returns
a sequence (C1, C2, ...).'''
    for e in l: f(*e)

def preserving_zip(*orig_seqs):
    '''A preserving zip which does not truncate to the length of the shortest sequence like the standard zip.
    seq1, seq2 = (1, 2), (3, 4, 5)
    zip(seq1, seq2) => ((1, 3), (2, 4))
    preserving_zip(seq1, seq2) => ((1, 3), (2, 4), (None, 5))'''
    seqs = map(lambda e: list(e)[::-1], orig_seqs)
    result = []
    
    def maybe_pop(seq):
        if not seq: return None
        else: return seq.pop()
        
    while any(seqs): # While some sequence is not empty
        result.append(map(maybe_pop, seqs))
    
    return result
    
