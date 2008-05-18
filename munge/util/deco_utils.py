from functools import update_wrapper

def cast_to(*types):
    '''A function decorator which takes a tuple of 1-arg constructor functions, modifying the decorated function
to cast each of its arguments with the corresponding constructor function before it is invoked. If the number of
formal arguments is fewer than the number of constructor functions, a RuntimeError is raised.

@cast_to(int, int)
def g(x, y):
    return x + y
    
g("2", "3") # => 5'''
    def f(func):
        tl = len(types)
        def _f(*args, **kwargs):
            if tl != len(args): raise RuntimeError("%d args expected, %d args received" % (tl, len(args)))
            return func(*(type(arg) for (type, arg) in zip(types, args)), **kwargs)
        return update_wrapper(_f, func)
    return f
    
import os
def filelike(f):
    '''Constructor which returns a file instance given a filename. If the given argument does not correspond to a file,
an exception is raised.'''
    if isinstance(f, basestring) and os.path.exists(f) and os.path.isfile(f):
        return file(f, 'r+')
    raise IOError('Argument %s is not a file.' % f)
    
def comma_list(f):
    return f.split(',')

def threshold(f):
    v = float(f)
    if 0.0 <= v <= 1.0:
        return v
    else:
        raise TypeError('Threshold must be in the range [0, 1].')
    
if __name__ == '__main__':
    @cast_to(int, int)
    def g(x,y):
        print x+y
        
    g("3", "4")
    g(3.5, "4")
    g(3,4,5)
    
