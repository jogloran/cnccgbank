from munge.proc.filter import Filter
from munge.cats.trace import analyse
from munge.trees.traverse import *
from munge.proc.tgrep.tgrep import tgrep, initialise, find_all

from collections import defaultdict

from munge.util.list_utils import *
from apps.cn.tag import is_np_internal_structure, ValidNPInternalTags
from itertools import imap
from apps.identify_pos import *

initialise()

def next_leaf(cur_leaf):
    while cur_leaf.parent and cur_leaf.parent.kids[-1] is cur_leaf:
        cur_leaf = cur_leaf.parent
        
    if not cur_leaf.parent: return None
    
    i = cur_leaf.parent.kids.index(cur_leaf)
    cur = cur_leaf.parent.kids[i+1]
    
    while (not cur.is_leaf()):
        cur = cur[0]
        
    return cur

def bin_lengths(l):
    if l <= 2: return l
    else: return 2

def make(filter_expression, node_filter_function=lambda _: True):
    class _(Filter):
        def __init__(self):
            self.sigs = defaultdict(lambda: [0, FixedSizeRandomList()])
        
            self.atboundary = defaultdict(lambda: [0, FixedSizeRandomList()])
        
        def accept_derivation(self, bundle):
            root = bundle.derivation
        
            for node, ctx in find_all(root, filter_expression, with_context=True):
                if node_filter_function(node):
                    words = list(text_without_quotes_or_traces(node))
                    words_filtered = list(text_without_quotes_or_traces(node, 
                        pred=lambda n: n.tag in ('NN', 'NR', 'NT', 'JJ') and not n.tag == "PU"))
            
                    lengths = [bin_lengths(len(w.decode('u8'))) for w in words_filtered]
                    if len(lengths)> 2 and lengths[0] == 1 and lengths[1] == 1: lengths[0:2] = [1]
                    lengths[1:-1] = []
                    sig = ' '.join(imap(str, lengths))
            
                    self.sigs[sig][0] += 1
                    self.sigs[sig][1].append(' '.join(words))
            
                    nn = next_leaf(node)
                    while nn and is_ignored(nn): nn = next_leaf(nn)
                    if not nn: continue
            
                    next_len = bin_lengths(len(nn.lex.decode('u8')))
                    key = '%s;%s' % (sig,next_len)
                    self.atboundary[key][0] += 1
                    self.atboundary[key][1].append(' '.join(words + ['* '+nn.lex]))
            
        def output(self):
            for k, (freq, examples) in sorted(self.sigs.iteritems(), key=lambda e: e[1], reverse=True):
                print '% 15s | %s' % (freq, k)
                print '%s | %s' % (' ' * 15, '; '.join(examples))
            print ">>>"
            for k, (freq, examples) in sorted(self.atboundary.iteritems(), key=lambda e: e[1], reverse=True):
                print '% 15s | %s' % (freq, k)
                print '%s | %s' % (' ' * 15, '; '.join(examples))
                
    return _
                
NP = make('NP < * ! #<1', is_np_internal_structure)
VO = make('VP < /VV/ < /NP/')
