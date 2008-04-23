import os
from munge.proc.trace import Filter  

from munge.vis.dot import write_graph
from munge.util.dict_utils import CountDict
from munge.cats.paths import applications  
from munge.proc.bases import CountWordFrequencyByCategory
from munge.proc.bases import AcceptRejectWithThreshold, AcceptRejectReporter

class WriteDOT(Filter):
    "Writes each derivation to a DOT file under the given directory."
    def __init__(self, output_dir):
        self.output_dir = output_dir
        
        try:
            os.mkdir(self.output_dir)
        except OSError: pass
    
    def accept_derivation(self, deriv):
        section_dir = "%02d" % deriv.sec_no
        doc_filename = "wsj_%02d%02d.%02d.dot" % (deriv.sec_no, deriv.doc_no, deriv.der_no)
        
        try:
            os.makedirs(os.path.join(self.output_dir, section_dir))
        except OSError: pass
        
        write_graph(deriv.derivation, os.path.join(self.output_dir, section_dir, doc_filename))
        
    opt = "w"
    long_opt = "write-graph"
    
    arg_names = "OUTDIR"
    
class ListCategoriesForLex(Filter):
    "Reports on all categories attested for a given lexical item."
    def __init__(self, lex):
        self.lex = lex
        self.cats_seen = set()
        
    def accept_leaf(self, leaf):
        if leaf.lex == self.lex:
            self.cats_seen.add( str(leaf.cat) )
            
    def output(self):
        print "%s |- %s" % (self.lex, ', '.join(cat for cat in sorted(self.cats_seen)))
        
    opt = "k"
    long_opt = "list-categories-for"
    
    arg_names = "LEX"
        
class CombinatorCounter(Filter):
    "Gives the frequency with which each combinator has been used."
    def __init__(self):
        self.counter = CountDict()
    
    def accept_leaf(self, leaf):
        appls = applications(leaf)
        for appl in appls:
            self.counter[ appl ] += 1
        
    def output(self):
        for comb, count in sorted(self.counter.iteritems(), cmp=lambda a, b: cmp(b[1], a[1])):
            print "% 20s | %d" % (comb, count)

    opt = "m"
    long_opt = "count-combinators"

class CollectExamples(CountWordFrequencyByCategory):
    def __init__(self, example_count):
        CountWordFrequencyByCategory.__init__(self)
        
        self.example_count = int(example_count)
        
    def output(self):
        for (cat, lex_dict) in self.examples.iteritems():
            print "Category %s:" % cat
            for (lex, frequency) in sorted(lex_dict.iteritems(), key=lambda (k, v): v, reverse=True)[0:self.example_count]:
                print "\t% 3d | %s" % (frequency, lex)       
            
    opt = "e"
    long_opt = "collect-examples"
    
    arg_names = "N"
    
# Do not change the order of inheritance; this would change the resolution order for output().
class NullModeCandidates(AcceptRejectReporter, AcceptRejectWithThreshold):
    '''Thresholding filter for the null mode (those reported as consumed by 'None').'''
    def __init__(self, threshold):
        AcceptRejectWithThreshold.__init__(self, threshold, (None,))

    opt = "z"
    long_opt = "list-null-mode-cands"

    arg_names = "THR"

# Do not change the order of inheritance; this would change the resolution order for output().
class ApplicationModeCandidates(AcceptRejectReporter, AcceptRejectWithThreshold):
    '''Thresholding filter for the application-only mode.'''
    def __init__(self, threshold):
        AcceptRejectWithThreshold.__init__(self, threshold, ("fwd_appl", "bwd_appl"))
        
    opt = "a"
    long_opt = "list-appl-mode-cands"

    arg_names = "THR"
