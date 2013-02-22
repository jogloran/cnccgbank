# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import find_all
from collections import defaultdict, Counter
from apps.util.tabulation import Tabulation
from apps.cn.fix_utils import base_tag
from munge.util.func_utils import compose2, compose, take
import operator

def signature(node):
    def stem_tag(tag):
        if tag.startswith('V') and tag[1] in 'VACE': return 'V'
        else: return base_tag(tag)
    return ' '.join(stem_tag(l.tag) for l in node if l.tag not in ('DER', 'AS', 'PU', 'AD', 'ADVP', 'FLR', 'SP'))

class Subcats(Tabulation(
        'frames', 
        value_maker=Counter, reducer=len, 
        additional_info_maker=compose(
            '; '.join, 
            lambda vs: map(lambda v: '\n\\glosE{%s}{}' % v, vs),
            lambda vs: map(operator.itemgetter(0), vs),
            lambda e: e.most_common(5)),
        separator='&',
        row_terminator=' ',
        additional_row_terminator='\\\\ \n',
        ),
    Filter):
    
    def __init__(self):
        super(Subcats, self).__init__()
        
    def accept_derivation(self, bundle):
        for node, ctx in find_all(bundle.derivation, r'/VP/ < /V[VACE]/=T ! < /CC/', with_context=True):
            lex = ':'.join(ctx.t.text())
            self.frames[signature(node)][lex] += 1
        
    def output(self):
        super(Subcats, self).output()