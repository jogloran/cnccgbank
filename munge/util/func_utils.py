const = lambda v: lambda: v
const_ = lambda v: lambda self: v

def compose2(f, g):
    '''Returns the composition of the two functions given.'''
    def h(*args, **kwargs):
        return f(g(*args, **kwargs))
    return h

def compose(*fs):
    fs = list(fs)
    result = fs.pop()
    while fs:
        result = compose2(fs.pop(), result)
    return result

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