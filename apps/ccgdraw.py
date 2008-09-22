from itertools import izip, count
import re, sys

def invert(l):
    h = {}
    for (e, i) in izip(l, count()):
        h[e] = i
    return h
'''
def get_spans_of(words):
    if not words: return []
    
    result = []
    start = 0
    skipping_whitespace = False
    for c, i in izip(words, count()):
        if c.isspace() and not skipping_whitespace:
            result.append( (start, i) )
            skipping_whitespace = True
        elif not c.isspace() and skipping_whitespace:
            start = i
            skipping_whitespace = False
            
    if not skipping_whitespace:
        result.append( (start, len(words)) )
            
    return result
    '''
    
span_pat = re.compile(r'\S+')
def get_spans_of(words):
    for r in span_pat.finditer(words):
        yield r.span()
        
def get_spans_and_text_of(words):
    for r in span_pat.finditer(words):
        yield (r.span(), r.group())
        
def transpose(xs):
    return map(list, zip(*xs))
    
def sanitise_category(cat):
    return re.sub(r'\\', r'\\bs ', cat)
        
def comb_lines(lines):
    ret = []
    
    by_row = transpose(lines)
        
    cur_column = 0
    arrow_line = []
    cat_line = []
    
    while by_row[0]:
        (begin, end), arrow = by_row[0].pop(0), by_row[1].pop(0)
        category = by_row[2].pop(0)
        
        combinator = get_combinator_for_arrow(arrow)
        if not combinator: raise RuntimeError('Unknown combinator.')
        
        arrow_line.append( " & " * (begin - cur_column) )
        arrow_line.append( "\\%s{%d}" % (combinator, end-begin+1) )
        
        cat_line.append( " & " * (begin - cur_column) )
        cat_line.append( "\mc{%d}{%s}" % (end-begin+1, sanitise_category(category)) )

        cur_column = end
        
    arrow_line.append('\\\\\n')
    cat_line.append('\\\\\n')
     
    return ''.join(''.join(line) for line in (arrow_line, cat_line))
    
tail_pat = re.compile(r'-+(.*)')
tails = {
    '>': 'fapply',
    '<': 'bapply',
    '>B': 'fcomp',
    '<B': 'bcomp',
    '>Bx': 'fxcomp',
    '<Bx': 'bxcomp',
    '>S': 'fsubst',
    '<S': 'bsubst',
    '>Sx': 'fxsubst',
    '<Sx': 'bxsubst',
    '>T': 'ftype',
    '<T': 'btype',
    '': 'uline'
}
def get_combinator_for_arrow(arrow):
    match = tail_pat.match(arrow)
    if match:
        tail_symbol = match.group(1)
        return tails[tail_symbol]
    
    return None
    
def word_lines(words):
    return (' & '.join('\\rm %s' % word for word in words) + '\\\\\n')
        

def process(lines, out=sys.stdout):
    lines.reverse()
    lines = [line for line in lines if line]
    
    words = lines.pop()
    spans = list(get_spans_of(words))
    
    out.write( word_lines(words.split()) )
    
    while lines:
        arrows, categories = lines.pop(), lines.pop()
        arrow_spans = list(get_spans_and_text_of(arrows))
        category_spans = list(get_spans_and_text_of(categories))

        to_write = []
        for (cbegin, cend), category in category_spans:
            for (abegin, aend), arrow in arrow_spans:
                if abegin <= cbegin <= cend < aend:
                    found = False
                    
                    for begin in xrange(len(spans)):
                        if found: break
                        
                        # Try the longest spans first (since they subsume smaller spans)
                        for end in xrange(len(spans)-1, -1, -1):
                            begin_index, end_index = spans[begin][0], spans[end][1]

                            if abegin <= begin_index <= end_index <= aend:
                                to_write.append( ((begin, end), arrow, category) )
                                
                                found = True
                                break # We want to break out of the begin,end nested loop
        
        out.write( comb_lines(to_write) )
        
if __name__ == '__main__':
    print r'''
\documentclass{article}
\usepackage{LI2}
\begin{document}
\deriv{9}{'''
    process(r'''
 The        quick brown fox jumped over the lazy dog
----------- ----- ----- --- ------ ---- --- ---- ---
     A        B      C   D   E       F   G   H    I
-------->Bx ----> --------<             ----------->
NP\NP        N/N      NP                       NP
------------------------>Bx        ---------------->
                NP\NP                    Q'''.split('\n'))
    print "}"
    print "\end{document}"