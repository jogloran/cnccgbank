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
set terminal x11 persist
set view map
set xtics border in scale 0,0 mirror norotate  offset character 0, 0, 0 autojustify
set ytics border in scale 0,0 mirror norotate  offset character 0, 0, 0 autojustify
set ztics border in scale 0,0 nomirror norotate  offset character 0, 0, 0 autojustify
set nocbtics
set rtics axis in scale 0,0 nomirror norotate  offset character 0, 0, 0 autojustify
set xrange [ -0.500000 : %(length)d ] noreverse nowriteback
set yrange [ 0.500000 : 1.5000 ] noreverse nowriteback
set cblabel "Score" 
set cbrange [ 0.00000 : %(max_value)d ] noreverse nowriteback
set palette rgbformulae 2, -7, -7
plot '-' using 2:1:3 with image
""" % dict(
    length=len(data),
    max_value=max(data),
)

for i, v in enumerate(data):
    print '0 %d %d' % (i, v)
    print '1 %d %d' % (i, v)

print 'e'
