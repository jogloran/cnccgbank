import sys, re, os
from itertools import groupby

BASEDIR = sys.argv[2]

pairs = []
lines = open(sys.argv[1], 'r').readlines()
while lines:
    pairs.append( (lines.pop(0), lines.pop(0)) )

def extract_section(pair):
    header = pair[0]
    matches = re.search(r'wsj_(\d\d)\d\d', header)
    if matches:
        return matches.group(1)
    else:
        raise Exception, "Couldn't find section header in line %s" % header

def extract_document(pair):
    header = pair[0]
    matches = re.search(r'wsj_\d\d(\d\d)', header)
    if matches:
        return matches.group(1)
    else:
        raise Exception, "Couldn't find document header in line %s" % header

for sec, docs in groupby(pairs, key=extract_section):
    path = os.path.join(BASEDIR, sec)
    if not os.path.exists(path): os.makedirs(path)

    for doc, derivs in groupby(docs, key=extract_document):
        with open(os.path.join(path, "chtb_%02d%02d.fid" % (int(sec), int(doc))), 'w') as f:
            for deriv in derivs:
                print >>f, deriv[0],
                print >>f, deriv[1],
