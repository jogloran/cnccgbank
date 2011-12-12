from apps.util.tabulation import Tabulation
from munge.proc.filter import Filter
from itertools import ifilter

class NCats(Tabulation('freqs'), Filter):
    def __init__(self):
        super(NCats, self).__init__()
        
    def accept_leaf(self, leaf):
        self.freqs[str(leaf.cat)] += 1
        
    def output(self):
        ncats = len(self.freqs)
        ncatsge10 = len(list(ifilter(lambda (k,v): v>=10, self.freqs.iteritems())))
        print "#cats     : %d" % ncats
        print "#cats >=10: %d" % ncatsge10