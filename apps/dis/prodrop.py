# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

# Find the most common verbs for which pro-drop applies

from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import tgrep, find_first, find_all

def find_head(node):
    cur = node
    while not cur.is_leaf():
        cur = cur[ cur.head_index ]
    return cur

from apps.util.tabulation import Tabulation
# order of superclasses is important
class ProdropCheck(Tabulation('verbs'), Filter):
    def __init__(self):
        super(ProdropCheck, self).__init__()
        
    def accept_derivation(self, bundle):
        top = bundle.derivation
        heads = set()
        for node, ctx in find_all(top, r'* $ { * < ^/\*pro\*/ }', with_context=True):
            head = find_head(node)
            if head not in heads:
                self.verbs[' '.join(head.text())] += 1
                heads.add(head)
                
class AllVerbsCheck(Tabulation('verbs'), Filter):
    def __init__(self):
        super(AllVerbsCheck, self).__init__() 
        
    def accept_derivation(self, bundle):
        top = bundle.derivation
        for node, ctx in find_all(top, r'/V[VACE]/', with_context=True):
            self.verbs[' '.join(node.text())] += 1