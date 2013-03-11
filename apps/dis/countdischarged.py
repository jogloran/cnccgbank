from munge.proc.filter import Filter
from itertools import imap
from apps.anno.nldfind import NLDFinder
from munge.proc.tgrep.tgrep import find_all
from munge.trees.traverse import text, leaves, get_index_of_leaf
from munge.trees.synttree import is_trace

import difflib

def align(o, n):
    matches = difflib.SequenceMatcher(a=o, b=n).get_matching_blocks()
    alignment = {}
    for match in matches:
        for i in xrange(match.size):
            alignment[match.a + i] = match.b + i
    return alignment

from collections import namedtuple, defaultdict
class Result(object):
    def __init__(self):
        self.discharged = self.not_discharged = 0
        
class CountDischargedTraces(Filter):
    Patterns = NLDFinder.Patterns
    
    def parse_toks_file(self, toks_file):
        return { label: tok_string.split() for (label, tok_string) in imap(lambda line: line.rstrip().split('|'), file(toks_file)) }
        
    def __init__(self, toks_file):
        # accepts a toks file of the final corpus and is meant to run on the original corpus
        super(CountDischargedTraces, self).__init__()
        
        self.toks = self.parse_toks_file(toks_file)
        self.results = defaultdict(Result)
        
    def accept_derivation(self, bundle):
        root = bundle.derivation
        for (pattern, name) in self.Patterns:
            # print pattern, name
            for node, ctx in find_all(root, pattern, with_context=True):
                toks = self.toks.get(bundle.label(), None)
                cn_toks = text(root)
                
                if not (toks and cn_toks):
                    print >>sys.stderr, bundle.label()
                
                alignment = align(cn_toks, toks)
                trace = ctx.t
                if trace is not None:
                    trace_index = get_index_of_leaf(root, trace)
                    if alignment.get(trace_index, None) is not None:
                        self.results[name].not_discharged += 1
                    else:
                        self.results[name].discharged += 1
                else:
                    print >>sys.stderr, "t was not bound to a trace node"
                            
    def output(self):
        for (nld_type, results) in self.results.iteritems():
            print '% 6d/% 6d = % 4.2f%% | %s' % (results.discharged, results.discharged + results.not_discharged, 
                results.discharged/float(results.discharged + results.not_discharged)*100.0,
                nld_type)