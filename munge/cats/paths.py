from itertools import imap, starmap
from munge.util.iter_utils import each_pair
from munge.cats.trace import analyse

def path_to_root(node):
    '''Yields a sequence of triples ( (l0, r0, f0), (l1, r1, f1), ... ) representing
    the path of a node and its sibling from the given _node_ up to the root.
    If f0 is true, then [l0 r0 -> r1]. Otherwise, [l0 r0 -> l1].'''
    while node.parent:
        if node.parent.rch == node:
            yield node.parent.lch, node, True
        elif node.parent.lch == node:
            yield node, node.parent.rch, False

        node = node.parent

    # Yield the root
    yield node, None, False

def category_path_to_root(node):
    '''Identical to path_to_root, except that the _categories_ of each node on
    the path are returned, instead of the nodes themselves.'''
    def extract_categories(left, right, was_flipped):
        return (left.cat, right.cat if right else None, was_flipped)
    return starmap(extract_categories, path_to_root(node))

def applications(node):
    '''Yields a sequence of rule applications starting from the given _node_ up to the root.'''
    for (prev_l, prev_r, _), (l, r, was_flipped) in each_pair(category_path_to_root(node)):
        yield analyse(prev_l, prev_r, r if was_flipped else l)
