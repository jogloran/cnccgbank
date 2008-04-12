from optparse import OptionParser
from itertools import izip, count
import sys
import os

from sets import Set

from munge.io.guess import GuessReader
from munge.trees.traverse import leaves
from munge.cats.paths import applications_per_slash
from munge.vis.dot import write_graph

class Filter(object):
    '''Every filter extends this class, which defines `don't care' implementations of the four hook
    functions. For each Derivation object (a bundle of the derivation object itself and some metadata),
    the framework calls each of the below methods.'''
    
    def accept_comb_and_slash_index(self, leaf, comb, slash_index, info=None):
        '''This is invoked by the framework for every slash of every category at a derivation leaf.'''
        pass
    def accept_leaf(self, leaf): 
        '''This is invoked by the framework for every derivation leaf.'''
        pass
    def accept_derivation(self, deriv): 
        '''This is invoked by the framework for each Derivation object.'''
        pass
    def output(self): 
        '''This is invoked by the framework after each derivation has been processed.'''
        pass
    
class WriteDOT(Filter):
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
        
    
class ListCategoriesForLex(Filter):
    def __init__(self, lex):
        self.lex = lex
        self.cats_seen = Set()
        
    def accept_leaf(self, leaf):
        if leaf.lex == self.lex:
            self.cats_seen.add( str(leaf.cat) )
            
    def output(self):
        print "%s |- %s" % (self.lex, ', '.join(cat for cat in sorted(self.cats_seen)))
    
def main(argv):
    parser = OptionParser()
    
    parser.set_defaults(verbose=True, filters=[WriteDOT('dots')])
    
    parser.add_option("-q", "--quiet", help="Suppress diagnostic messages.", 
                      action='store_false', dest='verbose')
    parser.add_option("-v", "--verbose", help="Print diagnostic messages.", 
                      action='store_true', dest='verbose')
    
    opts, remaining_args = parser.parse_args(argv)
    
    files = remaining_args[1:] # remaining_args[0] seems to be sys.argv[0]
    filters = opts.filters
    
    for file in files:
        print file
        for derivation in GuessReader(file):
            if opts.verbose: print >> sys.stderr, "Processing %s..." % derivation.label()
            
            for leaf in leaves(derivation.derivation):
                for filter in filters:
                    filter.accept_leaf(leaf)
                    
                    for comb, slash_index in izip(applications_per_slash(leaf), count()):
                        filter.accept_comb_and_slash_index(leaf, comb, slash_index)
                        
            filter.accept_derivation(derivation)
    
    for filter in filters:
        filter.output()
    
if __name__ == '__main__':
    main(sys.argv)