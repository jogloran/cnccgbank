#! /usr/bin/env python
import sys

from munge.io.guess import GuessReader
from munge.trees.pprint import pprint, pprint_petrov

if sys.argv[1][0] == '-': 
    petrov = True
    del sys.argv[1]
else:
    petrov = False

g = GuessReader(sys.argv[1])
for bundle in g:
    if petrov:
        print pprint_petrov(bundle.derivation, sep='', newline='')
    else:
        print pprint(bundle.derivation)
