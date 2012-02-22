# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.ccg.nodes import Leaf
from munge.cats.nodes import AtomicCategory

def make_open_quote_leaf(q, double=True):
    '''Creates an single or double open quote leaf above the given node.'''
    if q and not q.is_leaf():
        q = q.lch
        
    lex = "``" if double else "`"
    return Leaf(AtomicCategory('LQU'), 'LQU', 'LQU', lex, 'LQU', q)
    
def make_closed_quote_leaf(q, double=True):
    '''Creates an single or double close quote leaf above the given node.'''
    lex = "''" if double else "'"
    return Leaf(AtomicCategory('RQU'), 'RQU', 'RQU', lex, 'RQU', q)
