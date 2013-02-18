# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from apps.cn.output import OutputPrefacedPTBDerivation
from apps.cn.tag import is_np_internal_structure
from munge.trees.traverse import nodes, leaves

def has_np_label(node):
    return node.tag.startswith('NP')

class FlattenNP(Filter, OutputPrefacedPTBDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPrefacedPTBDerivation.__init__(self, outdir)
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if is_np_internal_structure(node):
                all_leaves = list(leaves(node))
                node.kids = all_leaves
                
        self.write_derivation(bundle)