from munge.proc.filter import Filter
from apps.cn.tag import is_coordination
from munge.trees.traverse import nodes
from munge.trees.pprint import pprint

class CommaCheck(Filter):
    def __init__(self):
        Filter.__init__(self)
        
    def accept_derivation(self, bundle):
        for node in nodes(bundle.derivation):
            if node.is_leaf(): continue
            if is_coordination(node):
                def get_tag(kid):
                    if kid.tag in ('CC', 'PU'): return kid.lex
                    else: return kid.tag
                print ' '.join(get_tag(kid) for kid in node)