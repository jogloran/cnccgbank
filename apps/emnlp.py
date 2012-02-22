# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.filter import Filter
from munge.proc.tgrep.tgrep import FixedTgrep, find_all, find_first
from munge.cats.trace import analyse
from munge.util.dict_utils import CountDict, sorted_by_value_desc

class CountRuleOccurrencesByType(FixedTgrep(r'''* <1 , | <2 ,''')):
    def __init__(self):
        CountRuleOccurrencesByType.__bases__[0].__init__(self)
        self.counts = CountDict()
        
    def match_generator(self, deriv, expr):
        return find_all(deriv, expr)
        
    def match_callback(self, match_node, bundle):
        key = analyse(match_node.lch.cat, match_node.rch.cat, match_node.cat)
        if key is None: key = 'other_typechange'
#            print "(%s %s -> %s) %s" % (match_node.lch.cat, match_node.rch.cat, match_node.cat, key)
        self.counts[key] += 1
        
    def output(self):
        for comb, freq in sorted_by_value_desc(self.counts):
            print "% 10s | %d" % (comb, freq)
            
class CountPunctuationTokens(Filter):
    Punctuation = (',', '.', ':', '`', '``', "'", "''", ';', '!', '?')
    
    def __init__(self):
        self.counts = CountDict()
        self.total = 0
        
    def accept_leaf(self, leaf):
        if leaf.lex in self.Punctuation:
            if leaf.lex == "'" and leaf.pos == 'POS': return
            
            self.counts[leaf.lex] += 1
        self.total += 1
        
    def output(self):
        for punct, f in sorted_by_value_desc(self.counts):
            print "%d | %s" % (f, punct)
        print "Total: %d" % self.total
        