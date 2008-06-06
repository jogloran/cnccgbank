from munge.trees.traverse import *
from munge.util.err_utils import *
from munge.penn.io import *
from munge.io.multi import *
from munge.cats.trace import *
import sys
from itertools import izip, count

LEFT_BRANCHING, RIGHT_BRANCHING = range(2)
make_all_commas = RIGHT_BRANCHING # (X ,)

def get_locator_sequence_to(leaf):
    ret = []
    cur = leaf
    while cur.parent is not None:
        ret.append('l' if cur.parent.lch is cur else 'r')
        cur = cur.parent
    return list(reversed(ret))
    
def fix_locator(locator, reattach_direction):
    if reattach_direction == RIGHT_BRANCHING:
        to_delete = 'l'
    else:
        to_delete = 'r'
        
    while locator[-1] == to_delete:
        del locator[-1]
                
    locator[-1] = 'l' if reattach_direction == RIGHT_BRANCHING else 'r'
    
    return locator

for bundle in DirFileGuessReader(sys.argv[1], verbose=False):
    for (leaf, index) in izip(leaves(bundle.derivation), count()):
        # exclude the case N (, N[conj]) -> N (we don't want to mess with the comma in this case)
        # but do include the case N[conj] (, N[conj]) (this is just absorption, not conjunction)
        if leaf.lex == ',':
            comma_is_left = leaf.parent.lch is leaf
            sibling = leaf.parent.rch if comma_is_left else leaf.parent.lch
            
            # Test if this is just absorption, not conjunction
            if leaf.parent.cat.has_feature('conj') and not sibling.cat.has_feature('conj'): continue
            # Test if this is an instance of comma typechange
            if (analyse(leaf.parent.lch.cat, leaf.parent.rch.cat, leaf.parent.cat) 
                not in ('l_punct_absorb', 'r_punct_absorb', 'conj_comma_absorb')): continue
            
            if make_all_commas == LEFT_BRANCHING:
                if comma_is_left: continue
            elif make_all_commas == RIGHT_BRANCHING:
                if not comma_is_left: continue
            
            print bundle.label()
            print "$%d S" % index#% ';'.join(str(l) for l in locator[:-1])
            print "@ A=,|,|,|,|"# % (';'.join(reattach_locator), command)
