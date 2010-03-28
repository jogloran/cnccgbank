from munge.proc.tgrep.tgrep import find_first

def get_first(*args, **kwargs):
    '''Returns one tgrep result, or None if no nodes match.'''
    try:
        return find_first(*args, **kwargs).next()
    except StopIteration:
        return None