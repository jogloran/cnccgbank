from functools import partial as curry

const = lambda v: lambda: v
const_ = lambda v: lambda self: v

identity = lambda v: v
noop = lambda *args, **kwargs: None

def compose2(f, g):
    '''Returns the composition of the two functions given.'''
    def h(*args, **kwargs):
        return f(g(*args, **kwargs))
    return h

from munge.util.deco_utils import seq_or_splat
@seq_or_splat
def compose(*fs):
    '''Returns the composition of any number of functions.'''
    fs = list(fs)
    if not fs:
        return identity
        
    result = fs.pop()
    while fs:
        result = compose2(fs.pop(), result)
    return result
    
@seq_or_splat
def chain_actions(*fs):
    '''Given a list of functions _fs_, returns a function g(*args, **kwargs) which applies its arguments to each
function in _fs_.'''
    def _g(*args, **kwargs):
        for f in fs:
            f(*args, **kwargs)
    return _g

noop_function = lambda *args, **kwargs: None

# satisfies_any(f1, f2...)(x) <=> any(f(x) for f in (f1, f2, ...))
def satisfies_any(*fs):
    def _f(*args, **kwargs):
        return any(f(*args, **kwargs) for f in fs)
        
    return _f
    
def satisfies_all(*fs):
    def _f(*args, **kwargs):
        satisfied = [False] * len(fs)
    
        for i, f in enumerate(fs):
            if f(*args, **kwargs): satisfied[i] = True
    
        return all(satisfied)
    
    return _f
    
def result_of(f):
    class _result(object):
        def __init__(self, func):
            self.func = func
        def __call__(self, *args, **kwargs):
            self.value = self.func(*args, **kwargs)
            return self.value
    return _result(f)
    
def deferred(f):
    class _deferred(object):
        def __init__(self, func):
            self.func = func
            self.value = None
        def __call__(self, *args, **kwargs):
            if not self.value:
                self.value = self.func(*args, **kwargs)
            return self.value
            
def n_times(n, f):
    '''Returns a function returning a list of the results of _n_
applications of _f_.'''
    # n_times(2, f)(1, 2, 3) => [ f(1, 2, 3), f(1, 2, 3) ]
    def _f(*args, **kwargs):
        return map(lambda f: f(*args, **kwargs), [f] * n)
    return _f
    
twice = curry(n_times, 2)
    
if __name__ == '__main__':
    even = lambda n: n % 2 == 0
    odd = lambda n: not even(n)
    gt1 = lambda n: n>1
    gt2 = lambda n: n>2
    lt1 = lambda n: n<1
    lt2 = lambda n: n<2
    print satisfies_any(even, odd)(3)
    print satisfies_all(even, odd)(3)
    print satisfies_any(gt1, gt2)(3)
    print satisfies_all(gt1, gt2)(3)
    print satisfies_any(lt1, lt2)(3)