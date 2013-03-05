from munge.proc.tgrep.tgrep import FixedTgrep, find_all, find_first
from collections import Counter, defaultdict
from munge.util.func_utils import const
from munge.util.dict_utils import sorted_by_value_desc
from munge.util.list_utils import FixedSizeList, FixedSizeRandomList
from apps.cn.fix_utils import base_tag

def signature(node, d):
    # return base_tag(k[0].tag) + ' ' + base_tag(k[-1].tag)
    dnp_index = [i for (i, k) in enumerate(node) if k.tag == 'DNP']
    last_nonpunct_tag = [k.tag for (i, k) in enumerate(node) if i < dnp_index and k.tag not in ('PU', 'PRN', 'FLR')][-1]
    return ' '.join( (base_tag(d[0].tag), base_tag(last_nonpunct_tag)) )

class CountModification(FixedTgrep(r'* < /DNP/=D')):
    '''Prints comma occurrence counts by descending frequency together with the rule used.'''
    def __init__(self):
        super(CountModification, self).__init__()
        self.counts = defaultdict(lambda: [0, FixedSizeRandomList(10)] )
        
    def output(self):
        for sig, (count, examples) in sorted_by_value_desc(self.counts):
            print '% 10d | %s' % (count, sig)
            print '; '.join(examples[:10])
        
    def match_generator(self, deriv, expr, with_context):
        return find_all(deriv, expr, with_context)
    
    def match_callback_with_context(self, node, bundle, ctx):
        self.counts[signature(node, ctx.d)][0] += 1
        
        example = ' '.join(node.text())
        if len(example) < 25:
            self.counts[signature(node, ctx.d)][1].append(example)
    
    def caption_generator(self, *args, **kwargs): pass
        
    @staticmethod
    def is_abstract(): return False
