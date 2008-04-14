from munge.proc.trace import Filter    

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
        
    
    long_opt = "write-graph"
    opt = "w"
    
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
        
from munge.util.dict_utils import CountDict
from munge.cats.paths import applications  
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
            
    @staticmethod
    def long_opt(): return "count-combinators"
    @staticmethod
    def opt(): return "m"

    opt = "m"
    long_opt = "count-combinators"
