# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from apps.util.tabulation import Tabulation
from munge.proc.filter import Filter
from munge.cats.trace import rooted_in_Sdcl
from apps.cn.fix_adverbs import is_modifier_category
from munge.cats.cat_defs import N, NP

def is_P_like(cat):
    return cat.is_complex() and is_modifier_category(cat.left) and \
        (not is_modifier_category(cat.right))

def categorise_category(cat):
    # V shaped
    if rooted_in_Sdcl(cat): return 'V'
    elif is_modifier_category(cat): return 'M'
    elif cat==N or cat==NP: return 'N'
    elif is_P_like(cat): return 'P'
    else: return '?'

class Shapes(Tabulation('shapes'), Filter):
    def __init__(self):
        super(Shapes, self).__init__()
        self.lexicon = set()
        
    def accept_leaf(self, leaf):
        if str(leaf.cat) not in self.lexicon:
            kategory = categorise_category(leaf.cat)
            #if kategory == '?': print leaf.cat
            self.shapes[ kategory ] += 1
            
            self.lexicon.add(str(leaf.cat))
