import sys
import ply.lex as lex
import ply.yacc as yacc

import munge.proc.tgrep.parse as parse
from munge.trees.traverse import nodes
from munge.util.iter_utils import take

from munge.proc.filter import Filter

_tgrep_debug = False

def initialise():
    lex.lex(module=parse)
    yacc.yacc(module=parse)

_tgrep_initialised = False
def tgrep(deriv, expression):
    global _tgrep_initialised
    
    if not expression: raise RuntimeError('No query expression given.')
    if not _tgrep_initialised:
        initialise()
        _tgrep_initialised = True
        
    if _tgrep_debug:
        lex.input(expression)
        for tok in iter(lex.token, None):
            print tok.type, tok.value

    query = yacc.parse(expression)
    for node in nodes(deriv):
        if query.is_satisfied_by(node):
            yield node
    
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
            TgrepCore.__init__(expression)
    return _TgrepCore
    
class TgrepException(Exception): pass
class Tgrep(TgrepCore):
    def show_node(match_node, bundle):
        print "%s: %s" % (bundle.label(), match_node)
        
    def show_tokens(match_node, bundle):
        print "%s: %s" % (bundle.label(), match_node.text())
        
    def show_label(match_node, bundle):
        print bundle.label()
        
    FIND_FIRST, FIND_ALL = range(2)
    find_functions = {
        FIND_FIRST: find_first,
        FIND_ALL:   find_all
    }

    SHOW_NODE, SHOW_TOKENS, SHOW_LABEL = range(3)
    match_callbacks = {
        SHOW_NODE: show_node,
        SHOW_TOKENS: show_tokens,
        SHOW_LABEL: show_label
    }
    
    def __init__(self, expression): #, mode=FIND_FIRST, show=SHOW_NODE):
        TgrepCore.__init__(self, expression)
        
        mode = self.FIND_FIRST
        show = self.SHOW_NODE
        
        if not Tgrep.is_valid_callback_key(mode, self.find_functions):
            raise TgrepException('Invalid Tgrep find mode %d given.' % mode)
        self.match_generator = Tgrep.find_functions[mode]
        
        if not Tgrep.is_valid_callback_key(show, self.match_callbacks):
            raise TgrepException('Invalid Tgrep show mode %d given.' % mode)
        self.match_callback = Tgrep.match_callbacks[show]
        
    @staticmethod
    def is_valid_callback_key(key, callbacks):
        return key in callbacks

    opt = 't'
    long_opt = 'tgrep'
    arg_names = 'EXPR'
