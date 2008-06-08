import sys
try:
    import ply.lex as lex
    import ply.yacc as yacc
except ImportError:
    import lex, yacc
    
class TgrepException(Exception): pass

import munge.proc.tgrep.parse as parse
from munge.trees.traverse import nodes, leaves
from munge.util.iter_utils import take

from munge.proc.filter import Filter

_tgrep_debug = False
_tgrep_initialised = False

def initialise():
    '''Performs lazy initialisation of the lexer and parser. Once called, further calls are no-ops.'''
    global _tgrep_initialised
    
    if not _tgrep_initialised:
        lex.lex(module=parse)
        yacc.yacc(module=parse)#, method='SLR')
    
        _tgrep_initialised = True

# quick and dirty memoisation. This is based on the exact string expression, so
# semantically identical expressions with trivial differences such as whitespace
# will not be considered identical
expression_cache = {}
def tgrep(deriv, expression):
    '''Performs the given tgrep query on the given tree.'''
    if not expression: raise RuntimeError('No query expression given.')

    if expression in expression_cache:
        query = expression_cache[expression]
        
    else:
        initialise()
            
        if _tgrep_debug:
            lex.input(expression)
            for tok in iter(lex.token, None):
                print tok.type, tok.value

        query = yacc.parse(expression)
        expression_cache[expression] = query
    
    for node in nodes(deriv):
        if query.is_satisfied_by(node):
            yield node
            
def multi_tgrep(deriv, query_callback_map):
    if not query_callback_map: raise RuntimeError('No query expressions given.')
    initialise()
    
    queries = [yacc.parse(expression) for expression in query_callback_map.keys()]
    for node in nodes(deriv):
        for query in queries:
            if query.is_satisfied_by(node):
                query_callback_map[query](node)
    
find_all = tgrep
find_first = lambda deriv, expr: take(find_all(deriv, expr), 1)

def matches(derivation, expression):
    return list(find_first(derivation, expression))
    
class TgrepCore(Filter):
    def __init__(self, expression):
        Filter.__init__(self)
        initialise()
        
        self.expression = expression
        
    def _not_implemented(self, *args):
        raise NotImplementedError('TgrepCore subclasses must implement match_generator and match_callback.')
    match_generator = _not_implemented
    match_callback = _not_implemented
        
    def accept_derivation(self, derivation_bundle):
        for match_node in self.match_generator(derivation_bundle.derivation, self.expression):
            self.match_callback(match_node, derivation_bundle)
            
def FixedTgrep(expression):
    class _TgrepCore(TgrepCore):
        def __init__(self):
            TgrepCore.__init__(self, expression)
    return _TgrepCore
    
class Tgrep(TgrepCore):
    def show_node(match_node, bundle):
        print "%s: %s" % (bundle.label(), match_node)

    def show_tree(match_node, bundle):
        print "%s: %s" % (bundle.label(), bundle.derivation)
        
    def show_tokens(match_node, bundle):
        print "%s: %s" % (bundle.label(), match_node.text())
        
    def show_label(match_node, bundle):
        print bundle.label()

    FIND_FIRST, FIND_ALL = range(2)
    find_functions = {
        FIND_FIRST: find_first,
        FIND_ALL:   find_all
    }

    SHOW_NODE, SHOW_TOKENS, SHOW_LABEL, SHOW_TREE = range(4)
    match_callbacks = {
        SHOW_NODE: show_node,
        SHOW_TOKENS: show_tokens,
        SHOW_LABEL: show_label,
        SHOW_TREE: show_tree
    }
    
    def get_callback_function(self, callback_key, callback_map):
        if callback_key not in callback_map:
            raise TgrepException('Invalid Tgrep mode %d given.' % callback_key)
        return callback_map[callback_key]
        
    def __init__(self, expression, find_mode=FIND_FIRST, show_mode=SHOW_NODE):
        TgrepCore.__init__(self, expression)
        
        self.find_mode = find_mode # node traversal strategy
        self.show_mode = show_mode # node output strategy
        
        self.match_generator = self.get_callback_function(find_mode, self.find_functions)
        self.match_callback  = self.get_callback_function(show_mode, self.match_callbacks)
        
    @staticmethod
    def is_valid_callback_key(key, callbacks):
        return key in callbacks

    opt = 't'
    long_opt = 'tgrep'
    arg_names = 'EXPR'

