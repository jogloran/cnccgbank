# Prints the deriv ID and leaf text from Penn-bracketed or CCGbank-bracketed text supplied on stdin

import sys
import re

def is_trace(m):
    return any(m.startswith(p) for p in ('*OP', '*pro', '*PRO', '*RNR', '*T', '*?', '*-'))

for line in sys.stdin:
    m = re.match(r'ID=wsj_(\d\d)(\d\d)\.(\d+)', line)
    if m:
        sec, doc, deriv = map(int, m.groups())
        print "%d %d %d" % (sec, doc, deriv),
    else:
        matches = re.findall(r'<L [^ ]+ [^ ]+ [^ ]+ ([^ ]+)', line)
        if matches: 
            print ' '.join(matches)
            continue

        matches = re.findall(r'\([^ ]+ ([^) ]+)\)', line)
        if matches: 
            print ' '.join(match for match in matches if not is_trace(match))

