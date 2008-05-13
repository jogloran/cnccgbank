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
        def _f(*args):
            if tl != len(args): raise RuntimeError("%d args expected, %d args received" % (tl, len(args)))
            return func(*(type(arg) for (type, arg) in zip(types, args)))
        return _f
    return f
    
import os
def filelike(f):
    '''Constructor which returns a file instance given a filename, otherwise returning the passed object untouched.'''
    if isinstance(f, basestring) and os.path.exists(f):
        return file(f, 'r+')
    return f
    
def comma_list(f):
    return f.split(',')
    
if __name__ == '__main__':
    @cast_to(int, int)
    def g(x,y):
        print x+y
        
    g("3", "4")
    g(3.5, "4")
    g(3,4,5)
    