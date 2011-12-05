from collections import defaultdict
import math

def decimal_length(n):
    return math.floor(math.log10(n) + 1)

def Tabulation(table_var):
    class _Tabulation(object):
        def __init__(self):
            setattr(self, table_var, defaultdict(int))
        
        def output(self):
            table = getattr(self, table_var)
            max_freq_length = decimal_length( max(table.values()) )
            template = "%% %sd | %%s" % (int(max_freq_length)+1)
            
            for k, freq in sorted(table.iteritems(), key=lambda e: e[1], reverse=True):
                print template % (freq, k)
        
    return _Tabulation