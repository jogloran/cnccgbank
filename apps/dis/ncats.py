# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

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