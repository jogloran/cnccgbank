# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from collections import defaultdict
import math

def decimal_length(n):
    '''Returns the length of _n_ in decimal digits. Undefined for n<0.'''
    return math.floor(math.log10(n) + 1)

def Tabulation(table_vars, reducer=lambda e:e, value_maker=int, limit=None):
    if not isinstance(table_vars, (list, tuple)):
        table_vars = [ table_vars ]
        
    class _Tabulation(object):
        def __init__(self):
            for table_var in table_vars:
                setattr(self, table_var, defaultdict(value_maker))
            self.reducer = reducer
        
        def output(self):
            self.do_output(self, reducer=reducer, limit=limit)
                
        def do_output(self, reducer=lambda x:x, limit=None):
            for table_var in table_vars:
                table = getattr(self, table_var)
                max_freq_length = decimal_length(reducer(max(table.values(), key=reducer)))
                
                template = "%% %sd | %%s" % (int(max_freq_length)+1)
            
                print "%s:" % table_var
                # a range endpoint of None corresponds to omitting the endpoint
                for k, freq in sorted(table.iteritems(), key=lambda e: reducer(e[1]), reverse=True)[:limit]:
                    freq = reducer(freq)
                    print template % (freq, k)
                print
        
    return _Tabulation