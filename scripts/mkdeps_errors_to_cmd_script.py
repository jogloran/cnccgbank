import sys, re

seen_deriv = None

print 'quiet'
print 'load apps.rulechk'
print 'into stdout'

for line in sys.stdin:
    line = line.rstrip()

    matches = re.search(r'Processing failed on derivation (\d+):(\d+)\((\d+)\)', line)
    if matches:
        seen_deriv = tuple(map(int, matches.groups()))

    matches = re.findall(r'`(\d+)', line)
    if matches:
        print 'with fixed_np/%d,%d,%d' % seen_deriv
        print '\n'.join( 'run CheckRules %s' % match for match in set(matches) )
