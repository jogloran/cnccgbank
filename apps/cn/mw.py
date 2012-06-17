import sys
import codecs
from itertools import ifilter
from collections import defaultdict

def head_arg_repr(lines):
    result = []
    for k, d in lines.items():
        head = d['head'].encode('u8') if d['head'] else None
        args = (arg.encode('u8') for arg in d['args'])
        # result.append( '%d (head: %s args: %s)' % (int(k),
        #     d['head'].encode('u8') if d['head'] else 'None',
        #     ', '.join(arg.encode('u8') for arg in d['args'])) )
        for arg in args:
            result.append( '%s %s' % (head, arg) )
    return '\n'.join(result)

def each_sentence(parg_lines):
    current = []
    while True:
        if not parg_lines: raise StopIteration        
        
        line = parg_lines.pop(0)
        
        if line.startswith('<s'):
            continue
        elif line.startswith('<\\s'):
            yield current
            current = []
        else:
            current.append(line.split())

if __name__ == '__main__':
    for fn in sys.argv[1:]:
        for sentence in each_sentence( codecs.open(fn, 'r', 'u8').readlines() ):
            lines = defaultdict(lambda: { 'head': None, 'args': [] })
            for parg in ifilter(
                lambda e: e[2] == r'(NP/NP)/M',
                sentence):
        
                # group by values of $2
                if parg[3] == '2':
                    lines[ parg[1] ]['head'] = parg[4]
                elif parg[3] == '1':
                    lines[ parg[1] ]['args'].append( parg[4] )
            
            if lines:
                print head_arg_repr(lines)