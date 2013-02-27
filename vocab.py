import sys
from collections import deque, Counter
from itertools import islice, chain

window_size = int(sys.argv[2])

class Deque(deque):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return islice(self, item.start, item.stop)
        else:
            return super(Deque, self).__getitem__(item)

window = Deque(maxlen=window_size * 3)

def inter(s, t):
    return len(set(s) & set(t))

n = 0

data = []

i = 0
for line in open(sys.argv[1]):
    toks = line.rstrip().split(' ')
    window.extend(toks)
    for t in toks:
        if n % window_size == 0:
            # left_intersection  = inter(window[:window_size], window[window_size:2*window_size])
            # right_intersection = inter(window[window_size:2*window_size], window[2*window_size:])

            left_intersection = sum(1 for k, v in Counter(window[window_size:2*window_size]).items() if v == 1)
            right_intersection = inter(chain(window[:window_size],window[2*window_size:]), window[window_size:2*window_size])
            data.append((left_intersection, right_intersection))
        n += 1

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
    max_value=max(chain(*data)),
)

for i, (l, r) in enumerate(data):
    print '0 %d %d' % (i, l)
    print '1 %d %d' % (i, r)

print 'e'
