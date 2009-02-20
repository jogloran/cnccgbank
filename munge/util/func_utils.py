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