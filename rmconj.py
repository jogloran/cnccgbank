#! /usr/bin/env python

# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

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
