import sys
from itertools import chain
from munge.trees.traverse import leaves, text_without_traces
from munge.io.guess import GuessReader

ranges = {
        ((0,0), (3,26)): 'xinhua',
        ((4,0), (4,55)): 'xinhua',
        ((6,0), (8,86)): 'xinhua',
        ((9,0), (9,32)): 'xinhua',
        ((5,0), (5,55)): 'hk',
        ((5,90), (5,97)): 'sinorama',
        ((9,0), (9,32)): 'xinhua',
        ((10,0),(11,52)): 'sinorama',
        ((20,0), (31,46)): 'bn'
}
indices = ['xinhua', 'hk', 'sinorama', 'bn', '?']

def find_source_for(s, d):
    for (start, end), source in ranges.iteritems():
        if (start <= (s, d) < end):
            return source
    return '?'

window_size = int(sys.argv[1])
nwords = 0
data = []
for fn in sys.argv[2:]:
    r = GuessReader(fn)
    for bundle in r:
        source = find_source_for(bundle.sec_no, bundle.doc_no)
        for leaf in text_without_traces(bundle.derivation):
            nwords += 1

            if nwords % window_size == 0:
                data.append(indices.index(source)+1)
    del r

print """
set terminal epslatex input color size 19cm, 4cm
set output 'corpusparts.tex'
set xrange [ -0.500000 : %(length)d ] noreverse nowriteback
set yrange [ 0.500000 : 1.5000 ] noreverse nowriteback
set palette defined ( 0 0.09765625 0.703125 0.56640625, 1 0.09765625 0.703125 0.56640625, 1 0.93359375 0.734375 0.0703125, 2 0.93359375 0.734375 0.0703125, 2 0.17578125 0.55078125 0.8359375, 3 0.17578125 0.55078125 0.8359375, 3 0.890625 0.2578125 0.20703125, 4 0.890625 0.2578125 0.20703125, 4 'white', 4 'white')
set cbtics ("" 0, "Xinhua" 1, "HKSAR" 2, "Sinorama" 3, "Broadcast" 4) scale 0
set cbrange [ 1 : %(max_value)d ] noreverse nowriteback
set xlabel "Number of words"
set xtics ( "0" 0, "100000" 5000, "200000" 10000, "300000" 15000, "400000" 20000, "500000" 25000, "600000" 30000, "700000" 35000 )
unset ytics
unset key
plot '-' using 2:1:3 with image
""" % dict(
    length=len(data),
    max_value=max(data),
)

for i, v in enumerate(data):
    print '0 %d %d' % (i, v)
    print '1 %d %d' % (i, v)

print 'e'
