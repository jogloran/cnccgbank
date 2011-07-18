import sys
try:
    import ply.lex as lex
    import ply.yacc as yacc
except ImportError:
    import lex, yacc

import munge.proc.tgrep.parse as parse
from munge.proc.tgrep.nodes import Context
from munge.trees.traverse import nodes, leaves, nodes_reversed, tag_and_lex, tag_and_text_under, lrp_repr
from munge.trees.pprint import pprint
from munge.util.iter_utils import take, single, intersperse
from munge.util.dict_utils import smash_key_case
from munge.util.err_utils import debug, info
from munge.util.func_utils import compose, chain_actions
from munge.util.iter_utils import take
from munge.util.exceptions import TgrepException
from functools import partial as curry
from itertools import izip, ifilter

from munge.proc.filter import Filter

_tgrep_debug = False
_tgrep_initialised = False

def initialise():
    '''Performs lazy initialisation of the lexer and parser. Once called, further calls are no-ops.'''
    global _tgrep_initialised
    
    if not _tgrep_initialised:
        lex.lex(module=parse)
        yacc.yacc(module=parse)
    
        _tgrep_initialised = True

# quick and dirty memoisation. This is based on the exact string expression, so
# semantically identical expressions with trivial differences such as whitespace
# will not be considered identical
expression_cache = {}
def tgrep(deriv, expression, with_context=False, nonrecursive=False, left_to_right=False):
    '''Performs the given tgrep query on the given tree. If _with_context_ is True, each matched node
yields a pair (node, context), and captured nodes are accessible by name using the dict-like context.
If the user wants to keep context around, a copy must be made.'''
    if not expression: raise RuntimeError('No query expression given.')

    if expression in expression_cache:
        query = expression_cache[expression]
        
    else:
        initialise()
            
        if _tgrep_debug:
            debug("Lexing %s", expression)
            lex.input(expression)
            for tok in iter(lex.token, None):
                debug("%s %s", tok.type, tok.value)

        query = yacc.parse(expression)
        expression_cache[expression] = query
    
    traversal_method = (single if nonrecursive  else 
                        nodes  if left_to_right else 
                        nodes_reversed)
                        
    context = Context()
    for node in traversal_method(deriv):
        context.clear()
        
        if query.is_satisfied_by(node, context):
            if _tgrep_debug: debug("%s matched %s", lrp_repr(node), query)
            if with_context:
                yield node, context
            else: yield node
            
def multi_tgrep(deriv, query_callback_map):
    if not query_callback_map: raise RuntimeError('No query expressions given.')
    initialise()
    
    if _tgrep_debug:
        for expression in query_callback_map.keys():
            debug("Lexing %s", expression)
            lex.input(expression)
            for tok in iter(lex.token, None):
                debug("\t%s %s", tok.type, tok.value)
    
    queries = [yacc.parse(expression) for expression in query_callback_map.keys()]
    for node in nodes(deriv):
        for query_expr, query_str in izip(queries, query_callback_map.keys()):
            context = Context()
            if query_expr.is_satisfied_by(node, context):
                if context:
                    query_callback_map[query_str](node, **smash_key_case(context))
                else:
                    query_callback_map[query_str](node)
    
find_all = tgrep
find_first = compose(curry(take, 1), find_all)

SmallSubtreeThreshold = 10
def find_small(*args, **kwargs):
    matches = tgrep(*args, **kwargs)
    with_context = kwargs['with_context']

    if with_context:
        return ifilter(lambda (match, context): match.leaf_count() <= SmallSubtreeThreshold,
                       matches)
    else:
        return ifilter(lambda match: match.leaf_count() <= SmallSubtreeThreshold, matches)
            
SmallSentenceThreshold = 25
def find_small_sents(*args, **kwargs):
    deriv = args[0]
    if deriv.leaf_count() > SmallSentenceThreshold: return iter([])
    else: return tgrep(*args, **kwargs)

def matches(derivation, expression):
    return list(find_first(derivation, expression))
    
def caption_label(bundle):
    sys.stdout.write(bundle.label())
def caption_nwords(bundle):
    sys.stdout.write(str(len(list(leaves(bundle.derivation)))))
    
def caption_space(bundle): sys.stdout.write(' ')
def caption_tab(bundle):   sys.stdout.write('\t')
def caption_newline(bundle): print
    
class TgrepCount(Filter):
    def __init__(self, expression):
        Filter.__init__(self)
        initialise()
        
        self.expression = expression
        self.count = 0
        self.total = 0
        
    def accept_derivation(self, bundle):
        if list(find_first(bundle.derivation, self.expression)): self.count += 1
        self.total += 1
        
    def output(self):
        if self.total > 0:
            print "%s matched %d/%d=(%0.2f%%)" % (
                self.expression, self.count, 
                self.total, self.count / float(self.total) * 100.0)
                
    opt = 'T'
    long_opt = 'tgrep-count'
    
    arg_names = 'EXPR'
    
class TgrepCore(Filter):
    '''Abstract filter class for a tgrep query. Subclasses must override match_generator and match_callback.'''
    def __init__(self, expression):
        Filter.__init__(self)
        initialise()
        
        self.expression = expression
        
        self.nmatched = self.total = 0
        
    def _not_implemented(self, *args):
        raise NotImplementedError('TgrepCore subclasses must implement match_generator and match_callback.')
    match_generator = _not_implemented
    match_callback = _not_implemented
    caption_generator = _not_implemented
        
    def accept_derivation(self, derivation_bundle):
        matched = False
        
        for match_node, context in self.match_generator(derivation_bundle.derivation, self.expression, with_context=True):
            self.caption_generator(derivation_bundle)
            self.match_callback(match_node, derivation_bundle)
            if not matched: matched = True
            
        if matched:
            self.nmatched += 1
        self.total += 1
    
    @staticmethod
    def is_abstract(): return True
            
def FixedTgrep(expression):
    class _TgrepCore(TgrepCore):
        def __init__(self):
            TgrepCore.__init__(self, expression)
    return _TgrepCore
    
class Tgrep(TgrepCore):
    def output(self):
        deriv_percentage = 0 if self.total == 0 else self.nmatched/float(self.total)*100.0
        print "matches: %d/%d derivs = %.2f%%" % (self.nmatched, self.total, deriv_percentage)
        
    @staticmethod
    def show_none(match_node, bundle): pass
        
    @staticmethod
    def show_node(match_node, bundle):
        print match_node
        
    @staticmethod
    def show_pp_node(match_node, bundle):
        print pprint(match_node)

    @staticmethod
    def show_tree(match_node, bundle):
        print bundle.derivation
        
    @staticmethod
    def show_pp_tree(match_node, bundle):
        print pprint(bundle.derivation)
        
    @staticmethod
    def show_tokens(match_node, bundle):
        print ''.join(match_node.text())
        
    @staticmethod
    def show_label(match_node, bundle):
        print bundle.label()
        
    @staticmethod
    def show_rule(match_node, bundle):
        if match_node.is_leaf():
            print "(%s)" % match_node.cat
        else:
            print "(%s -> %s)" % (' '.join(kid.cat for kid in match_node), match_node.cat)
                
    @staticmethod
    def show_tags(match_node, bundle):
        print match_node.__repr__(suppress_lex=True)
        
    @staticmethod
    def show_matched_tag(match_node, bundle):
        print match_node.tag
        
    @staticmethod
    def show_tags_and_text(node, bundle):
        def node_print(node):
            if node.is_leaf():
                return tag_and_lex(node)
            else:
                return "%s (%s)" % (node.tag, " ".join(tag_and_text_under(x) for x in node))
        
        if node.is_leaf():
            print tag_and_lex(node)
        else:
            if node.rch:
                print "%s %s -> %s" % tuple(map(node_print, (node.lch, node.rch, node)))
            else:
                print "%s -> %s" % tuple(map(node_print, (node.lch, node)))

    FIND_FIRST, FIND_ALL, FIND_SMALL, FIND_SMALL_SENTS = range(4)
    find_functions = {
        FIND_FIRST: find_first,
        FIND_ALL:   find_all,
        FIND_SMALL: find_small,
        FIND_SMALL_SENTS: find_small_sents
    }
    
    def get_show_function(self, callback_key):
        valid_keys = set(func[5:] for func in dir(self) if func.startswith('show_'))

        if callback_key not in valid_keys:
            raise TgrepException('Invalid Tgrep mode %s given.' % callback_key)
        return getattr(self, 'show_' + callback_key)
        
    def get_find_function(self, callback_key):
        if callback_key not in self.find_functions:
            raise TgrepException('Invalid Tgrep find mode %s given.' % callback_key)
        return self.find_functions[callback_key]
    
    CAPTION_LABEL, CAPTION_NWORDS, CAPTION_SPACE, CAPTION_NEWLINE = range(4)
    caption_functions = {
        CAPTION_LABEL:  caption_label,
        CAPTION_NWORDS: caption_nwords,
        CAPTION_SPACE: caption_space,
        CAPTION_NEWLINE: caption_newline,
    }
    def get_caption_function(self, callback_key):
        if callback_key not in self.caption_functions:
            raise TgrepException('Invalid Tgrep caption type %s given.' % callback_key)
        return self.caption_functions[callback_key]
        
    def __init__(self, expression, find_mode=FIND_FIRST, show_mode='node', caption_modes=None):
        TgrepCore.__init__(self, expression)
        
        if caption_modes is None:
            # apply default caption modes if none given
            caption_modes = [Tgrep.CAPTION_LABEL, Tgrep.CAPTION_NWORDS, Tgrep.CAPTION_NEWLINE]
        
        self.find_mode = find_mode # node traversal strategy
        self.show_mode = show_mode # node output strategy
        
        self.match_generator = self.get_find_function(find_mode)
        self.match_callback  = self.get_show_function(show_mode)
        self.caption_generator = chain_actions(
            intersperse((self.get_caption_function(key) for key in caption_modes),
                        spacer=caption_space))
        
    @staticmethod
    def is_valid_callback_key(key, callbacks):
        return key in callbacks
        
    @staticmethod
    def is_abstract(): return False

    opt = 't'
    long_opt = 'tgrep'
    arg_names = 'EXPR'
