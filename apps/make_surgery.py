from munge.trees.traverse import *
from munge.util.err_utils import *
from munge.penn.io import *
import sys

for line in sys.stdin.readlines():
    line = line.rstrip()
    matches = re.match(r'(\d+):(\d+)\((\d+)\)', line)
    sec, doc, deriv = map(int, matches.groups())

    r = PTBReader(os.path.join('wsj', "%02d" % sec, "wsj_%02d%02d.mrg" % (sec, doc)))
    tree = r[deriv]
    text = tree.text()

    if text[-1] in ('``', '`'):
        print line
        print "-1 d"

        print "%d:%d(%d)" % (sec, doc, deriv+1)
        if text[-1] == "``":
            print "0 i=``|``"
        elif text[-1] == "`":
            print "0 i=``|`"
            
        debug("%s ends with start quote", line)
    elif text[0] in ("''", "'"):
        print line
        print "0 d"

        print "%d:%d(%d)" % (sec, doc, deriv-1)
        if text[0] == "''":
            print "e i=''|''"
        elif text[0] == "`":
            print "e i=''|'"
            
        debug("%s begins with end quote", line)

