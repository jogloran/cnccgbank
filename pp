#! /usr/bin/env python
import sys

from munge.io.guess import GuessReader
from munge.trees.pprint import pprint

g = GuessReader(sys.argv[1])
for bundle in g:
    print pprint(bundle.derivation)
    print
