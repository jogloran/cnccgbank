# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.trees.traverse import *
from munge.util.err_utils import *
from munge.penn.io import *
from munge.io.multi import *
import sys

for bundle in DirFileGuessReader(sys.argv[1], verbose=False):
    tree = bundle.derivation
    text = tree.text()
    sec, doc, deriv = bundle.spec_tuple()

    if text[-1] in ('``', '`'):
        print bundle.label()
        print "-1 d"

        print "%d:%d(%d)" % (sec, doc, deriv+1)
        if text[-1] == "``":
            print "0 i=``|``"
        elif text[-1] == "`":
            print "0 i=``|`"
            
        debug("%s ends with start quote", bundle.label())
    elif text[0] in ("''", "'"):
        print bundle.label()
        print "0 d"

        print "%d:%d(%d)" % (sec, doc, deriv-1)
        if text[0] == "''":
            print "e i=''|''"
        elif text[0] == "`":
            print "e i=''|'"
            
        debug("%s begins with end quote", bundle.label())

