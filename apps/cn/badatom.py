import re
from munge.proc.filter import Filter
from apps.cn.output import OutputPrefacedPTBDerivation
from munge.trees.traverse import nodes, leaves
from munge.penn.nodes import Leaf
from apps.cn.fix_utils import replace_kid
from munge.util.config import config

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
            print '>',subcat
            return True
        return False
    return any( f(subcat) for subcat in atom_list(cat) )

class BadAtom(Filter, OutputPrefacedPTBDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPrefacedPTBDerivation.__init__(self, outdir)
        
    def accept(self, root):
        for node in nodes(root):
            cat = node.cat
            
            if has_bad_subcat(cat):
                return False
        return True

    MergedTags = { 'VCD', 'VNV', 'VPT' }
    def accept_derivation(self, bundle):
        if self.accept(bundle.derivation):
            self.write_derivation(bundle)
            
    arg_names = 'OUTDIR'
