# A port of the Ruby abbrev module.

import re
from collections import defaultdict

def re_rindex(regex, string):
    n = len(string)
    for (char, index) in zip(reversed(string), xrange(n, -1, -1)):
        if re.search(regex, char):
            return index
    return -1

def abbrev(words, pattern=None):
    table = {}
    seen = defaultdict(lambda x: 0)
    
    if isinstance(pattern, basestring):
        pattern = "^%s" % re.escape(pattern)
        
    for word in words:
        abbrev = word
        if len(abbrev) == 0: continue
        
        while True:
            length = re_rindex(r'[\w\W]\z', abbrev)
            if length > 0:
                abbrev = word[0:length]
                if pattern is not None and not (re.search(pattern, abbrev)):
                    continue
            
                seen[abbrev] += 1
                if seen[abbrev] == 1:
                    table[abbrev] = word
                elif seen[abbrev] == 2:
                    del table[abbrev]
                else:
                    break
            else:
                break
                
    for word in words:
        if pattern is not None and not (re.search(pattern, word)):
            continue
            
        table[word] = word
        
    return table
            