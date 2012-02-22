# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from apps.cn.output import OutputPrefacedPTBDerivation
from apps.cn.fix_utils import replace_kid
from apps.cn.fix_rc import get_trace_index_from_tag
from munge.proc.tgrep.tgrep import find_all
from munge.trees.traverse import leaves

import re

index_re = re.compile(r'\*T\*-(\d+)$')
def find_coindexed_trace(parent, trace_node):
    index = get_trace_index_from_tag(trace_node.tag)
    for kid in leaves(parent):
        match = index_re.match(kid.lex)
        if match and match.group(1) == index[1:]:
            return kid
    return None
    
class UndoTop(Filter, OutputPrefacedPTBDerivation):
    def __init__(self, outdir):
        Filter.__init__(self)
        OutputPrefacedPTBDerivation.__init__(self, outdir)
        
    def accept_derivation(self, bundle):
        top = bundle.derivation
        for node, ctx in find_all(top, r'* < /-TPC-\d/a=T', with_context=True):
            trace = find_coindexed_trace(top, ctx.t)
            if trace:
                topicalised_node = ctx.t
                
                topicalised_node.tag = trace.parent.tag
                replace_kid(trace.parent.parent, trace.parent, topicalised_node)
                node.kids.remove(topicalised_node)
                
        self.write_derivation(bundle)