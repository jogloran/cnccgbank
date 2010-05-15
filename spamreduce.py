import os, math

MACHINES = 9
sections = '00 01 02 03 04 05 06 07 08 09 10 11 20 21 22 23 24 25 26 27 28 29 30 31'.split()

def at_a_time(seq, n):
    i = 0
    while i < len(seq):
        yield seq[i:i+n]
        i += n

each = int(math.ceil(len(sections)/float(MACHINES)))
for (i, portion) in enumerate(at_a_time(sections, each)):
    os.system("ssh -f dtse6695@nlp%d.it.usyd.edu.au \"cd /n/nlp0/u2/daniel/tools && ./make_base.sh %s\"" % (i, ' '.join(portion)))
