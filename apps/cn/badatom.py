# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import os
import re
from collections import defaultdict
from munge.proc.filter import Filter
from apps.cn.output import OutputPrefacedPTBDerivation
from munge.trees.traverse import nodes, leaves
from munge.penn.nodes import Leaf
from apps.cn.fix_utils import replace_kid
from munge.util.config import config
from munge.util.dict_utils import sorted_by_value_desc

GoodCats = set(("LCP", "M", "QP", "N", "NP", "PP", "S", 
                "conj", "LRB", "RRB", "LCM", "LPA", "RPA", 
                "LQU", "RQU", "LSQ", "RSQ", "LTL", "RTL", 
                "LCD", "RCD", "LCS", "RCS", "?", "!", "DSH", ".", ",", ";", ":"))
                
def atom_categories(cat):
    if cat.is_complex():
        for atom_cat in atom_categories(cat.left):
            yield atom_cat
        for atom_cat in atom_categories(cat.right):
            yield atom_cat
    else:
        yield cat

def atom_list(cat):
    def canonicalise(C):
        return re.sub(r'\[[^]]+\]', '', str(C))
    return set( canonicalise(C) for C in atom_categories(cat) )

def has_bad_subcat(cat):
    def f(subcat):
        if subcat not in GoodCats:
            #print '>',subcat
            return True
        return False
    return any( f(subcat) for subcat in atom_list(cat) )

class BadAtom(Filter, OutputPrefacedPTBDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPrefacedPTBDerivation.__init__(self, outdir)

        self.outdir = outdir
        self.bad = OutputPrefacedPTBDerivation(os.path.join(outdir, 'failed'))
        self.bad_freqs = defaultdict(int)
        
    def accept(self, root):
        for node in nodes(root):
            cat = node.cat
            
            if has_bad_subcat(cat):
                self.bad_freqs[str(cat)] += 1
                return False
        return True

    MergedTags = { 'VCD', 'VNV', 'VPT' }
    def accept_derivation(self, bundle):
        if self.accept(bundle.derivation):
            self.write_derivation(bundle)
        else:
            self.bad.write_derivation(bundle)

    def output(self):
        with file(os.path.join(self.outdir, 'failed_freqs'), 'w') as f:
            for badcat, freq in sorted_by_value_desc(self.bad_freqs):
                print >>f, '% 5d | %s' % (freq, badcat)
            
    arg_names = 'OUTDIR'
