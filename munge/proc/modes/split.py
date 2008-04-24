from __future__ import with_statement
from collections import defaultdict
from itertools import izip, count
import re, os

from munge.proc.trace import Filter
from munge.proc.modes.treeop import percolate, ModeTier
from munge.cats.parse import parse_category
from munge.util.err_utils import warn, debug
from munge.util.exceptions import FilterException
from munge.util.list_utils import find
from munge.cats.paths import applications_per_slash
from munge.util.iter_utils import reject
from munge.cats.nodes import APPLY, COMP, NULL, ALL


class DerivationOutput(object):
    '''Mix-in which writes each derivation to a file.'''   
    def write_derivation(self, deriv, output_dir):
        output_path = os.path.join(output_dir, 'AUTO', "%02d" % deriv.sec_no)
        if not os.path.exists(output_path): os.makedirs(output_path)

        output_filename = os.path.join(output_path, "wsj_%02d%02d.auto" % (deriv.sec_no, deriv.doc_no))
        # TODO: write PARG too (for this filter it would suffice to copy them unchanged)
        with file(output_filename, 'a') as output_file:
            print >> output_file, deriv.header()
            print >> output_file, deriv.derivation

class Subst(DerivationOutput, Filter):
    '''Substitutes categories based on a map.'''
    def __init__(self, substs, output_dir):
        # substs maps from the _name_ of each old category to its replacement category _object_.
        self.substs = substs
        self.output_dir = output_dir
        
    def accept_leaf(self, leaf):
        cat_string_without_modes = leaf.cat.__repr__(show_modes=False) # Hide modes
        if cat_string_without_modes in self.substs:
            debug("Substituting %s with %s", cat_string_without_modes, self.substs[cat_string_without_modes])
            leaf.cat = self.substs[cat_string_without_modes]
    
    def accept_derivation(self, deriv):
        percolate(deriv.derivation)
        self.write_derivation(deriv, self.output_dir)
        
    opt = "s"
    long_opt = "subst"
    
    arg_names = "SUBSTS,OUTDIR"
    
class SubstFromAnnotatorFile(Filter):
    '''Performs category substitution given an annotator file.'''
    def __init__(self, anno_filename, output_dir):
        self.anno_filename = anno_filename
        self.substs = self.process_annotator_into_substs(anno_filename)
        self.output_dir = output_dir
        
        self.filter = Subst(self.substs, self.output_dir)
        
    def accept_leaf(self, leaf):
        self.filter.accept_leaf(leaf)
        
    def accept_derivation(self, deriv):
        self.filter.accept_derivation(deriv)
        
    mode_string_map = {
        "null": NULL,
        "apply": APPLY,
        "comp": COMP,
        "all": ALL
    }
    def mode_string_to_index(self, mode_string):
        if mode_string not in self.mode_string_map:
            raise FilterException, "Invalid mode string %s encountered in annotator file." % mode_string
        
        return self.mode_string_map[mode_string]
        
    def process_annotator_into_substs(self, fn):
        substs = {}
        
        slashes = defaultdict(set)
        with file(fn, 'r') as f:
            for (line, lineno) in izip(f, count()):
                line = line.rstrip()
                
                fields = line.split()
                if len(fields) != 3:
                    raise FilterException, ("Missing field at line %d of annotator file %s." 
                                            % (lineno, self.anno_filename))
                                            
                category_string, replacement_mode_string, slash_index = fields
                debug("Slash %s of %s goes to %s=%d" % (slash_index, re.sub(r'[-.*@]', '', category_string), replacement_mode_string,self.mode_string_to_index(replacement_mode_string)))
                slashes[re.sub(r'[-.*@]', '', category_string)].add(
                                        ( int(slash_index), self.mode_string_to_index(replacement_mode_string) ))
                
            for (category_string, replacements) in slashes.iteritems():
                moded_category = parse_category(category_string)
                moded_category.labelled()
                
                for (subcategory, slash_index) in moded_category.slashes():
                    result = find(lambda (index, mode): index == slash_index, replacements)
                    if result:
                        replacement_slash, replacement_mode = result
                        debug("Setting mode of slash %s of %s to %s", slash_index, moded_category, replacement_mode)
                        subcategory.mode = replacement_mode
                        
                substs[category_string] = moded_category
        
        return substs
                    
    opt = "F"
    long_opt = "subst-from-anno"
    
    arg_names = "ANNO,OUTDIR"
        
class AssignModeSplit(DerivationOutput, Filter):
    '''Implements mode splitting, weakening modes as much as possible while maintaining existing analyses.'''
    def load_splitdef_file(self, splitdef_file):
        cats_to_split = []
        permitted_cats = defaultdict(list)
        
        reading_splits = True
        
        with file(splitdef_file, 'r') as def_file:
            for line in def_file:
                line = line.rstrip()
                
                if line == "%":
                    reading_splits = False
                    continue
                
                if reading_splits:
                    cat, slash = line.split()
                    cats_to_split.append( (parse_category(cat), int(slash)) )
                else:
                    old, new = line.split()
                    old = re.sub(r'[-.*@]', '', old)
                    
                    permitted_cats[old].append( parse_category(new) )
        
        return cats_to_split, permitted_cats
        
    def __init__(self, splitdef_file, output_dir):
        self.cats_to_split, self.permitted_cats = self.load_splitdef_file(splitdef_file)
        self.output_dir = output_dir
        
    def modes_for_cat(self, cat):
        if cat.is_leaf(): return []
        
        return [c.mode for (c, slash_index) in cat.slashes()]
        
    def mode_on_slash(self, cat, slash_index):
        for ((subcategory, _), cur_slash_index) in izip(cat.slashes(), count()):
            if cur_slash_index == slash_index:
                return subcategory.mode
                
        return None
        
    def permissiveness(self, cat, ignored_slash_index):
        result = 0
        for ((subcategory, _), cur_slash_index) in izip(cat.slashes(), count()):
            if cur_slash_index != ignored_slash_index:
                result += ModeTier[subcategory.mode] * (cur_slash_index + 1)
        
        return result
        
    def fix_cat_for(self, leaf, slash_index, mode):
        key_category = re.sub(r'[-.*@]', '', str(leaf.cat))
        if not (key_category in self.permitted_cats):
            warn("No entry in splitdef file for category %s" % str(leaf.cat))
            return
            
        alternatives = self.permitted_cats[key_category]
        #print "All alternatives: %s" % alternatives
            
        old_modes = self.modes_for_cat(leaf.cat)
        
        def is_invalid_alternative(alt):
            alt_modes = self.modes_for_cat(alt)
            if len(alt_modes) != len(old_modes):
                warn("Replacement category %s has different size to original category %s" % (str(alt), str(leaf.cat)))
                
            modes_for_comparison = zip(alt_modes, old_modes)
            del modes_for_comparison[slash_index]

            return str(leaf.cat) == str(alt) or \
                   any((ModeTier[alt] < ModeTier[old]) for (alt, old) in modes_for_comparison)
                   
        valids = list(reject(alternatives, is_invalid_alternative))
        if not valids:
            warn("No valid alternative for %s which preserves mode `%s' on slash %d", leaf.cat, mode, slash_index)
            return
            
        #print "Alternatives: %s" % valids
        alternative = min(valids, key=lambda e: self.permissiveness(e, slash_index))
        debug("%s `%s' -> %s" % (leaf.cat, leaf.lex, alternative))
        
        leaf.cat = alternative
        
    def accept_leaf(self, leaf):
        result = find(lambda (c, i): (c == leaf.cat), self.cats_to_split)
        if not (result and leaf.cat.is_compound()): return
        
        cat, slash_index = result
        
        appls = list(applications_per_slash(leaf, False))
        try:
            appl = appls[slash_index]
            if str(appl).endswith('comp'):
                if self.mode_on_slash(leaf.cat, slash_index) != COMP:
                    self.fix_cat_for(leaf, slash_index, "comp")
                    
            elif str(appl).endswith('appl'):
                if self.mode_on_slash(leaf.cat, slash_index) != APPLY:
                    self.fix_cat_for(leaf, slash_index, "apply")
                    
        except IndexError:
            pass
        
    
    def accept_derivation(self, deriv):
        percolate(deriv.derivation)
        self.write_derivation(deriv, self.output_dir)
                
    opt = "S"
    long_opt = "split"
    
    arg_names = "DEF_FILE,OUTDIR"
