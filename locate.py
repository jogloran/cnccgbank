#! /usr/bin/env python

import sys
import re
import os

sought = set(sys.argv[1:])
corpus = 'corpora/cptb/segmented'

XML, PLAIN = 1, 2
def determine_format_from(line):
    if line.startswith('<DOC'): return XML
    else: return PLAIN

for path, dirs, files in os.walk(corpus):
    for fn in files:
        if not fn.endswith('.seg'): continue
        
        doc_sent_no = 0
        lines = open(os.path.join(path, fn), 'r').xreadlines()

        format = None
        first = True

        try:
            while True:
                line = lines.next()
                if first:
                    format = determine_format_from(line)
                    first = False

                if format == XML:
                    if line.startswith('<S ID'):
                        doc_sent_no += 1
                        candidate = set(lines.next().rstrip().split())

                        if sought <= candidate:
                            print fn, doc_sent_no
                else:
                    doc_sent_no += 1
                    candidate = set(line.rstrip().split())

                    if sought <= candidate:
                        print fn, doc_sent_no


        except StopIteration: pass
