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