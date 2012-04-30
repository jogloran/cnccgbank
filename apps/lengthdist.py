import glob, os, math
from munge.proc.trace_core import TraceCore

def as_slices(L, K):
    '''Yields slices from _L_ of length _K_ each.'''
    if K <= 0: raise ValueError('required: k > 0')
    i = 0
    while i < len(L):
        yield L[i:i+K]
        i += K

def segmented_corpora(topdir, N):
    '''Divides the files under _topdir_ into N groups of approximately equal size.'''
    def all_files():
        for file in glob.glob(os.path.join(topdir, '**')):
            if not os.path.isfile(file): continue
            yield file
    files = list(all_files())
    return as_slices(files, int(math.ceil(len(files)/N)))

if __name__ == '__main__':
    trace = TraceCore(['apps.sanity'], verbose=False)
    
    topdir = 'cn'
    N = 10
    
    for files in segmented_corpora(topdir, 10):
        print '%s...%s' % (files[0], files[-1])
        trace.run( [('SanityChecks', None)], files )