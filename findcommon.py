# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

# Given two files both containing lines of the form:
# 0 1 2 text
# this reports how many lines with the first three columns matching have different values of 'text'
# The first file's contents should be a superset of the second's contents
import sys

fn1, fn2 = sys.argv[1], sys.argv[2]
f1, f2 = iter(file(fn1)), iter(file(fn2))

def same_doc(b1, b2):
    return b1[:3] == b2[:3]

def same_text(b1, b2):
    return b1[3:] == b2[3:]

count = 0
# l1 is the more complete
while True:
    try:
        l1 = f1.next().rstrip()
    except StopIteration: break
    l2 = f2.next().rstrip()

    b1 = l1.split(' ')
    b2 = l2.split(' ')

    while not same_doc(b1, b2) and f1:
        l1 = f1.next().rstrip()
        b1 = l1.split(' ')

    if not same_text(b1, b2):
        print >>sys.stderr, "-\n\t%s\n\t%s" % (l1, l2)
        count += 1

print "%d unequal" % count
