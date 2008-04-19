from munge.proc.trace import Filter
from munge.proc.modes.treeop import percolate

class SubstituteAtLeaves(Filter):
    def __init__(self, substs):
        # substs maps from the _name_ of the old category to its replacement category _object_.
        self.substs = substs
        
    def accept_leaf(self, leaf):
        cat_string_without_modes = str(leaf.cat, show_modes=False) # Hide modes
        if cat_string_without_modes in self.substs:
            leaf.cat = self.substs[cat_string_without_modes]
    
    def accept_derivation(self, deriv):
        percolate(deriv)
        
    opt = "s"
    long_opt = "subst-file"
    
    arg_names = "FILE"
        
class AssignModeSplit(Filter):
    def __init__(self, cats_to_split, permitted_cats):
        pass
         
    def modes_for_cat(self, cat):
        pass
        
    def permissiveness(self, cat, exc):
        pass
        
    def fix_cat_for(self, leaf, slash_index, mode):
        pass
        
    def accept_leaf(self, leaf):
        pass
        
    def accept_derivation(self, deriv):
        percolate(deriv)
        
    opt = "S"
    long_opt = "split"
    
    arg_names = "DEF_FILE"