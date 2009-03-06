from munge.proc.tgrep.tgrep import find_first

def get_first(*args, **kwargs):
    try:
        return find_first(*args, **kwargs).next()
    except StopIteration:
        return None