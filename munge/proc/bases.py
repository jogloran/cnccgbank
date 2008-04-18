from collections import defaultdict

from munge.util.dict_utils import CountDict
from munge.proc.trace import Filter

class CountRuleFrequencyBySlash(Filter):
    '''Abstract filter which counts how many times each combinator is used for each slash of each category.'''
    def __init__(self):
        self.freqs = CountDict()
        
    def accept_comb_and_slash_index(self, leaf, comb, slash_index):
        self.freqs[ (str(leaf.cat), comb, slash_index) ] += 1
        
class CountWordFrequencyByCategory(Filter):
    '''Abstract filter which counts the number of times each lexical item occurs for each category.'''
    def __init__(self):
        self.examples = defaultdict(CountDict)
        
    def accept_leaf(self, leaf):
        self.examples[ str(leaf.cat) ][leaf.lex] += 1
        
class ListCounts(CountRuleFrequencyBySlash):
    def output(self):
        for (cat, comb, slash_index), frequency in sorted(self.freqs.iteritems(), key=lambda e: e[1], reverse=True):
            print "% 60s | %2d | %25s | %d" % (cat, slash_index, comb, frequency)
        
class AcceptRejectWithThreshold(CountRuleFrequencyBySlash):
    '''Filter implementing a method which partitions every slash of every category into two sets:
    a slash/combinator entry is _accepted_ if it is consumed by one of the allowed combinators at least
    a given proportion of the time. It is _rejected_ otherwise.'''
    
    def __init__(self, threshold, allowed_combs):
        CountRuleFrequencyBySlash.__init__(self)
        
        self.threshold = float(threshold)
        self.allowed_combs = allowed_combs
        
    def compute_accepts_and_rejects(self):
        '''Partitions the slash/combinator entries into accept or reject sets based on their frequency.'''

        all_uses_per_slash = defaultdict(list)
        for (cat, comb, slash_index), frequency in self.freqs.iteritems():
            all_uses_per_slash[ (str(cat), slash_index) ].append( (comb, frequency) )
                                                     
        accepted, rejected = [], []
        
        for (cat, slash_index), entry in all_uses_per_slash.iteritems():
            accepted_frequency = total_frequency = 0
 
            for (comb, frequency) in entry:
                if comb in self.allowed_combs:
                    accepted_frequency += frequency
                total_frequency += frequency
                
            entry = (cat, slash_index, accepted_frequency, total_frequency)
            if accepted_frequency / float(total_frequency) >= self.threshold:
                accepted.append(entry)
            else:
                rejected.append(entry)
        
        return accepted, rejected
    
    def output(self):
        accepted, rejected = self.compute_accepts_and_rejects()

        for set in (accepted, rejected):
            for (cat, slash_index, applied_frequency, total_frequency) in \
                sorted(set, key=lambda this: this[2], reverse=True): # Third index is frequency
                percentage = applied_frequency / float(total_frequency) * 100.0

                print "% 60s | %2d | %5d /%5d (%3.2f%%) " % (cat, slash_index, applied_frequency, total_frequency, percentage)
            print "-" * 100
        