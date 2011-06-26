#! /usr/bin/env python

import sys
import re
import fileinput
preface = None
for line in fileinput.input():
    if line.startswith('ID'): preface = line
    else:
        if not re.search(r'<L [^ ]+\[conj\]', line):
            sys.stdout.write(preface)
            sys.stdout.write(line)
