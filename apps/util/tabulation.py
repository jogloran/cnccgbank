from collections import defaultdict
import math

def decimal_length(n):
    '''Returns the length of _n_ in decimal digits. Undefined for n<0.'''
    return math.floor(math.log10(n) + 1)

def Tabulation(table_var, reducer=lambda e:e, value_maker=int, limit=None):
    class _Tabulation(object):
        def __init__(self):
            setattr(self, table_var, defaultdict(value_maker))
            self.reducer = reducer
        
        def output(self):
            table = getattr(self, table_var)
            max_freq_length = decimal_length(reducer(max(table.values(), key=reducer)))
                
            template = "%% %sd | %%s" % (int(max_freq_length)+1)
            
            # a range endpoint of None corresponds to omitting the endpoint
            for k, freq in sorted(table.iteritems(), key=lambda e: reducer(e[1]), reverse=True)[:limit]:
                freq = reducer(freq)
                print template % (freq, k)
        
    return _Tabulation