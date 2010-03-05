def do_pad_split(splitter, str, sep, maxsplit):
    ret = splitter(str, sep, maxsplit) 
    ret += [None] * (maxsplit+1 - len(ret))
    return ret
    
padded_split  = lambda *args: do_pad_split(str.split,  *args)
padded_rsplit = lambda *args: do_pad_split(str.rsplit, *args)

def nth_occurrence(seq, N, when, until):
    n = 0
    buffer = []
    recording = False
    
    for element in seq:
        if when(element) and not recording:
            n += 1
            recording = True
            
        if recording and n == N:
            buffer.append(element)
            
        if until(element):
            recording = False
            if n > N: break
            
    return buffer
            
if __name__ == '__main__':
    # 0 1 2 3 4 5 6 7 8 9
    print nth_occurrence(range(10) + range(7,14), 2, when=lambda n: n>=6, until=lambda n: n>8)