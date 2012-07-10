# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from functools import partial as curry

def do_pad_split(splitter, str, sep, maxsplit):
    '''Splits the string, but pads the result tuple to the maximum number of allowable
sub-strings, as defined by _maxsplit_.'''
    ret = splitter(str, sep, maxsplit) 
    ret += [None] * (maxsplit+1 - len(ret))
    return ret
    
padded_split  = curry(do_pad_split, str.split)
padded_rsplit = curry(do_pad_split, str.rsplit)

def nth_occurrence(seq, N, when, until):
    '''Given a sequence _seq_, this returns the _n_th sub-sequence for which
the predicate _when_ is true, with _until_ defining the end of each sub-sequence.
The returned sub-sequence does not include the line where _until_ is True.'''
    n = 0
    buffer = []
    recording = False
    
    for element in seq:
        if until(element):
            recording = False
            if n > N: break

        if when(element) and not recording:
            n += 1
            recording = True
            
        if recording and n == N:
            buffer.append(element)
            
            
    return buffer
    
def gloss_tokenise(gloss_string):
    '''
>>> list(gloss_tokenise("This is a test ."))
['This', 'is', 'a', 'test', '.']
>>> list(gloss_tokenise("This is a {test of the function} ."))
['This', 'is', 'a', 'test of the function', '.']
>>> list(gloss_tokenise("{test of the function}"))
['test of the function']
>>> list(gloss_tokenise("{}"))
['']
>>> list(gloss_tokenise(""))
[]
>>> list(gloss_tokenise("a a {test of the function} b b"))
['a', 'a', 'test of the function', 'b', 'b']
'''
    def _find(needle, haystack, start=None):
        index = haystack.find(needle, start)
        return None if index == -1 else index
        
    while gloss_string != '':
        if gloss_string[0] == '{':
            index_to_trim_to = _find('}', gloss_string) # missing } -> till end of line
            yield gloss_string[1:index_to_trim_to]      # skip past opening {
            
            # skip till after next ws token
            index_to_trim_to = _find(' ', gloss_string, start=index_to_trim_to)
        else:
            index_to_trim_to = _find(' ', gloss_string)
            yield gloss_string[:index_to_trim_to]
            
        if index_to_trim_to is None: raise StopIteration
        gloss_string = gloss_string[index_to_trim_to+1:]

if __name__ == '__main__':
    import doctest
    doctest.testmod()