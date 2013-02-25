from munge.proc.filter import Filter
from collections import defaultdict, Counter

class AdjDist(Filter):
    def __init__(self):
        Filter.__init__(self)
        class D(object):
            def __init__(self):
                self.va = 0
                self.jj = 0
                self.va_examples = Counter()
                self.jj_examples = Counter()
                self.mixed_examples = Counter()
            def __repr__(self): return '<va:%d, jj:%d>' % (self.va, self.jj)
            
        self.counts = defaultdict(D)
        
    def accept_leaf(self, leaf):
        if leaf.tag == 'VA':
            self.counts[leaf.lex].va += 1
            self.counts[leaf.lex].va_examples[leaf.lex] += 1
        elif leaf.tag == 'JJ':
            self.counts[leaf.lex].jj += 1
            self.counts[leaf.lex].jj_examples[leaf.lex] += 1
        else:
            self.counts[leaf.lex].mixed_examples[leaf.lex] += 1
    
    def output(self):
        def perc(n, denom):
            return (n, denom, n/float(denom)*100.0)
        A, B, C = 0, 0, 0
        Ax, Bx, Cx = Counter(), Counter(), Counter()
        for j, counts in self.counts.iteritems():
            if counts.jj == 0:
                A += 1
                Ax[j] += counts.va
            elif counts.va == 0:
                B += 1
                Bx[j] += counts.jj
            else:
                C += 1
                Cx[j] += counts.va + counts.jj
                
        # A: exclusively VA
        # |jj==0|/|counts|
        print 'A: %d/%d=%.2f%%' % perc(A, len(self.counts))
        print '; '.join(r'\glosE{%s}{}' % e[0] for e in Ax.most_common(20))
                
        # B: exclusively JJ
        # |va==0|/|counts|
        print 'B: %d/%d=%.2f%%' % perc(B, len(self.counts))        
        print '; '.join(r'\glosE{%s}{}' % e[0] for e in Bx.most_common(20))
        # C: mix
        # |jj!=0&&va!=0|/|counts|
        print 'C: %d/%d=%.2f%%' % perc(C, len(self.counts))
        print '; '.join(r'\glosE{%s}{}' % e[0] for e in Cx.most_common(20))