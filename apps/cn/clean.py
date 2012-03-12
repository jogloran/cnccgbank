# coding: utf-8
# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from apps.cn.output import OutputPrefacedPTBDerivation
from munge.trees.traverse import nodes, leaves
from munge.penn.nodes import Leaf, Node
from apps.cn.fix_utils import replace_kid
from munge.util.config import config

INTERPUNCT = '·'

merge_verb_compounds = config.merge_verb_compounds
normalise_foreign_names = config.normalise_foreign_names

class Clean(Filter, OutputPrefacedPTBDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPrefacedPTBDerivation.__init__(self, outdir)
        
    # def accept(self, root):
    #     return not any(node.tag.startswith('UCP') for node in nodes(root))
    #           
    # def accept_derivation(self, bundle):
    #     if self.accept(bundle.derivation):
    #         self.write_derivation(bundle)
    #def accept(self, root):
    #    return any(leaf.lex == '*pro*' for leaf in leaves(root))
    def accept(self, root): return True

    @staticmethod
    def is_candidate_foreign_name(name):
        return INTERPUNCT in name

    MergedTags = { 'VCD', 'VNV', 'VPT' }
    def accept_derivation(self, bundle):
        global merge_verb_compounds
        if merge_verb_compounds:
            for node in nodes(bundle.derivation):
                if node.tag in self.MergedTags:
                    replace_kid(node.parent, node, Leaf(node.tag, ''.join(kid.lex for kid in leaves(node)), node.parent))

        if normalise_foreign_names:
            for leaf in leaves(bundle.derivation):
                if self.is_candidate_foreign_name(leaf.lex):
                    kids = [ Leaf(leaf.tag, bit, None) for bit in leaf.lex.split(INTERPUNCT) ]
                    replace_kid(leaf.parent, leaf, Node('NP-PN', kids))

        if self.accept(bundle.derivation):
            self.write_derivation(bundle)
            
    long_opt = 'clean'
    arg_names = 'OUTDIR'
