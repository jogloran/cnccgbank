from itertools import izip, count

def first_index_such_that(pred, l):
    for e, i in izip(list(l), count()):
        if pred(e): return i
    return None
    
def last_index_such_that(pred, l):
    return first_index_such_that(pred, reversed(list(l)))
    
def is_sublist(smaller, larger):
    m = len(smaller)
    for start in range(0, (len(larger) - m + 1) + 1):
        if larger[start:(start+m)] == smaller: return True
        
    return False
    
def find(pred, l):
    for e in l:
        if pred(e): return e
        
    return None