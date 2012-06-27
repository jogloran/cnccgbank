from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import find_all
from apps.util.tabulation import Tabulation
from apps.cn.fix_utils import base_tag

from collections import defaultdict

def signature(node):
    def ignored(tag):
        return tag == 'AS' or tag == 'PU' or tag == 'PRN' or tag == 'FLR'
    return ' '.join(base_tag(k.tag) for k in node[1:] if not ignored(k.tag))

class SubcatFrames(Tabulation('frames'), Filter):
    def __init__(self):
        super(SubcatFrames, self).__init__()

    def accept_derivation(self, bundle):
        for node in find_all(bundle.derivation, '* <1 /VV/'):
            self.frames[signature(node)] += 1
