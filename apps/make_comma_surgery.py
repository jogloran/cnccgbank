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

for bundle in DirFileGuessReader(sys.argv[1]):
    for (leaf, index) in izip(leaves(bundle.derivation), count()):
        if leaf.lex == ',' and not leaf.parent.cat.has_feature('conj'):
            # Test if this is an instance of comma typechange
            if analyse(leaf.parent.lch.cat, leaf.parent.rch.cat, leaf.parent.cat) != 'l_punct_absorb': continue
            
            if make_all_commas == LEFT_BRANCHING:
                if leaf.parent.lch is leaf: continue
            elif make_all_commas == RIGHT_BRANCHING:
                if leaf.parent.rch is leaf: continue
            
            print bundle.label()
            
            #locator = get_locator_sequence_to(leaf)
            # shrink parent of leaf (locator[:-1])
            print "$%d S" % index#% ';'.join(str(l) for l in locator[:-1])
            
            # reattach comma as high as possible in the other subtree
#            if make_all_commas == RIGHT_BRANCHING:
                # delete 'l's from the end of the locator sequence, then replace the last 'r' with 'l'
                # then append
            #reattach_locator = fix_locator(locator, make_all_commas)
                
            #command = "A" if locator[-1] == 'l' else "P"
            #print "%s %s=,|,|,|,|" % (';'.join(reattach_locator), command)
            print "@ A=,|,|,|,|"# % (';'.join(reattach_locator), command)