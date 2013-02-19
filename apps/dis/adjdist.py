from munge.proc.filter import Filter
from collections import defaultdict

class AdjDist(Filter):
    def __init__(self):
        Filter.__init__(self)
        class D(object):
            def __init__(self):
                self.va = 0
                self.jj = 0
            def __repr__(self): return '<va:%d, jj:%d>' % (self.va, self.jj)
            
        self.counts = defaultdict(D)
        
    def accept_leaf(self, leaf):
        if leaf.tag == 'VA':
            self.counts[leaf.lex].va += 1
        elif leaf.tag == 'JJ':
            self.counts[leaf.lex].jj += 1
    
    def output(self):
        def perc(n, denom):
            return (n, denom, n/float(denom)*100.0)
        A, B, C = 0, 0, 0
        for j, counts in self.counts.iteritems():
            if counts.jj == 0:
                A += 1
            elif counts.va == 0:
                B += 1
            else:
                C += 1
                
        # A: exclusively VA
        # |jj==0|/|counts|
        print 'A: %d/%d=%.2f%%' % perc(A, len(self.counts))
        # B: exclusively JJ
        # |va==0|/|counts|
        print 'B: %d/%d=%.2f%%' % perc(B, len(self.counts))        
        # C: mix
        # |jj!=0&&va!=0|/|counts|
        print 'C: %d/%d=%.2f%%' % perc(C, len(self.counts))        