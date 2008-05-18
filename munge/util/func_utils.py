def compose(f, g):
    '''Returns the composition of the two functions given.'''
    def h(*args, **kwargs):
        return f(g(*args, **kwargs))
    return h
