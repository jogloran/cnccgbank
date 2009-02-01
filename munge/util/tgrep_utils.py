from munge.proc.tgrep.tgrep import find_first

def get_first(node, expr):
    try:
        return find_first(node, expr).next()
    except StopIteration:
        return None