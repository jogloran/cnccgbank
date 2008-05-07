from itertools import imap, starmap, tee
from munge.util.iter_utils import each_pair
from munge.cats.trace import analyse
from munge.cats.labels import label_result

def preserving_zip(*orig_seqs):
    seqs = map(lambda e: list(e)[::-1], orig_seqs)
    result = []
    
    def maybe_pop(seq):
        if not seq: return None
        else: return seq.pop()
        
    while any(seqs):
        result.append(map(maybe_pop, seqs))
    print seqs
    
    return result
    
def simple_path_to_root(node):
    while node:
        yield node
        node = node.parent

def lca(node1, node2):
    if not node1: return node2
    if not node2: return node1

    path1 = simple_path_to_root(node1)
    path2 = simple_path_to_root(node2)
    
    pred = None
    
    for (node1, node2) in preserving_zip(path1, path2):
        if node1 == node2:
            pred = node1
        else:
            return pred
            
    return pred

def path_to_root(node):
    '''Yields a sequence of triples ( (l0, r0, f0), (l1, r1, f1), ... ) representing
    the path of a node and its sibling from the given _node_ up to the root.
    If f0 is true, then r0 is the 'focus' of the triple. Otherwise, l0 is. The focus
    is the node which actually lies on the sought path, the non-focus node is its sibling.'''
    while node.parent:
        if node.parent.rch is node:
            yield node.parent.lch, node, True
        elif node.parent.lch is node:
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
    
def cloned_category_path_to_root(node):
    '''Identical to path_to_root, except that the _categories_ of each node on
    the path are returned, instead of the nodes themselves.'''
    def extract_categories(left, right, was_flipped):
        return (left.cat.clone(), right.cat.clone() if right else None, was_flipped)

    return starmap(extract_categories, path_to_root(node))

def applications(node):
    '''Yields a sequence of rule applications starting from the given _node_ up to the root.'''
    return applications_with_path(category_path_to_root(node))
        
def applications_with_path(path):
    '''Yields a sequence of rule applications applied along a _path_ to the root.'''
    for (prev_l, prev_r, _), (l, r, was_flipped) in each_pair(path):
        yield analyse(prev_l, prev_r, r if was_flipped else l)
        
def applications_per_slash(node, examine_modes=False):
    '''Returns a list of length _n_, the number of slashes in the category of _node_.
    Index _i_ in this list denotes the combinatory rule which consumed slash _i_.'''
    return applications_per_slash_with_path(cloned_category_path_to_root(node),
                                            node.cat.slash_count(),
                                            examine_modes)

def applications_per_slash_with_path(orig_path, slash_count, examine_modes=False):
    result = []

    for slash in range(slash_count):
        consumer = None # the rule which consumed this slash, if any
        first = True
        
        # We need to copy the path for each slash, because in each iteration we label
        # the categories in-place.
        orig_path, path = tee(orig_path, 2)
        
        for (prev_l, prev_r, prev_was_flipped), (l, r, was_flipped) in each_pair(path):
            if first:
                if prev_was_flipped and prev_r:
                    prev_r.labelled()
                elif not prev_was_flipped:
                    prev_l.labelled()
                first = False

            cur      = r      if was_flipped      else l
            prev_cur = prev_r if prev_was_flipped else prev_l

            rule = analyse(prev_l, prev_r, cur, examine_modes)
            label_result(cur, prev_cur, rule, prev_was_flipped)

            if   rule == 'fwd_appl': consumed_category = prev_l
            elif rule == 'bwd_appl': consumed_category = prev_r
            elif rule in ('fwd_comp', 'bwd_comp', 'bwd_xcomp', 'fwd_xcomp'): consumed_category = prev_cur
            else: consumed_category = None

            if consumed_category and consumed_category.label == slash:
                consumer = rule
                break

        result.append( consumer )

    return result
