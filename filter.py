#! /usr/bin/env python
# coding: utf-8

import sys, re
from itertools import imap

lines = imap(lambda l: l[:-1], open(sys.argv[1], 'r').readlines())

def get_words(line):
    return ' '.join(re.findall(r'<L [^ ]+ [^ ]+ [^ ]+ ([^ ]+)', line))

while True:
    try:
        idline = lines.next()
        sentline = lines.next()
    except StopIteration: break

    words = get_words(sentline)

    if (re.match(r'^新华社.+(对外部|记者|电)', words) and
        not re.match(r'。$', words)): continue
    if words.startswith('（ 完 ）'): continue
    if re.search(r'wsj_1073.23', idline) or re.search(r'wsj_1128.31', idline): continue

    print idline
    print sentline
