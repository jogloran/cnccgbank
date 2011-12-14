from munge.proc.filter import Filter
from apps.cn.output import OutputPrefacedPTBDerivation
from apps.cn.fix_utils import replace_kid
from apps.cn.fix_rc import get_trace_index_from_tag
from munge.proc.tgrep.tgrep import find_all
from munge.trees.traverse import leaves

def find_coindexed_trace(parent, trace_node):
    index = get_trace_index_from_tag(trace_node.tag)
    for kid in leaves(parent):
        if kid.lex.startswith('*T*') and (kid.lex.find(index) != -1): 
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