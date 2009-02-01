try:
    import ply.lex as lex
    import ply.yacc as yacc
except ImportError:
    import lex, yacc

import sys, re

import munge.ccg.nodes as ccg
from munge.cats.cat_defs import C
from munge.util.err_utils import warn, err
from munge.proc.tgrep.nodes import *
from munge.proc.tgrep.tgrep import TgrepException

tokens = ("LPAREN", "RPAREN", "ATOM", "OP", "REGEX", 
          "QUOTED", "PIPE", "BANG", "LT", "GT", "EQUAL", "STAR", "TILDE", "CARET")

precedence = (
    ('right', 'PIPE'),
    ('right', 'BANG')
)

def t_PIPE(t):
    r'\|'
    return t
    
def t_BANG(t):
    r'!'
    return t
    
def t_LT(t):
    r'\['
    return t
    
def t_GT(t):
    r'\]'
    return t
    
def t_EQUAL(t):
    r'='
    return t

def t_STAR(t):
    r'\*'
    return t
    
def t_TILDE(t):
    r'~'
    return t

# Assume no whitespace is permitted within a regex.
def t_REGEX(t):
    r'/([^/\s]|\/)+/'
    return t

def t_LPAREN(t):
    r'\{'
    return t
def t_RPAREN(t):
    r'\}'
    return t

def t_QUOTED(t):
    r'"[^"]+"'
    return t

def t_CARET(t):
    r'\^'
    return t

# Productions need to be sorted by descending length (maximal munch)
def t_OP(t):
    r'(<<,?|>>\'?|(<-?\d?)|>|\.\.?|\$\.?\.?)'
    return t

def t_ATOM(t):
    r'''[^/\\"\s{][^\s]+[^/\\"\s}]|[^/\\\s{][^/\\\s}]|[^/\\\s{}]'''
    return t
    
# ignore whitespace tokens
t_ignore = ' \t\r\v\f\n'

def t_error(t):
    warn("Illegal character `%s' encountered.", t.value[0])
    t.lexer.skip(1)
    
def p_error(stk):
    err("Syntax error encountered: %s", stk)
        
def p_node(stk):
    '''
    node : matcher
         | node constraint_list
    '''
    if len(stk) == 2:
        stk[0] = Node(stk[1])
    elif len(stk) == 3:
        stk[0] = stk[1]
        stk[0].constraints.extend(stk[2])
            
def p_constraint_list(stk):
    '''
    constraint_list : constraint constraint_list
                    | constraint
    '''
    if len(stk) == 3:
        stk[0] = [stk[1]] + stk[2]
    elif len(stk) == 2:
        stk[0] = [stk[1]]
        
def p_constraint(stk):
    '''
    constraint : constraint_group
               | op matcher
               | BANG constraint
               | constraint PIPE constraint
    '''
    if len(stk) == 2:
        stk[0] = stk[1]
    elif len(stk) == 3:
        if stk[1] == '!':
            stk[0] = Negation(stk[2])
        else:
            stk[0] = Constraint(stk[1], stk[2])
            
    elif len(stk) == 4:
        stk[0] = Alternation(stk[1], stk[3])

def p_op(stk):
    '''
    op : OP
    '''
    stk[0] = stk[1]
        
def p_constraint_group(stk):
    '''
    constraint_group : LT constraint_list GT
    '''
    stk[0] = ConstraintGroup(stk[2])
                
def p_group(stk):
    '''
    group : LPAREN node RPAREN
    '''
    stk[0] = Group(stk[2])
    
def p_matcher(stk):
    '''
    matcher : atom 
            | regex
            | quoted
            | star
            | group
            | EQUAL ATOM
            | TILDE ATOM
            | matcher EQUAL ATOM
            | CARET ATOM
            | CARET QUOTED
    '''
    if len(stk) == 2:
        stk[0] = stk[1]
    elif len(stk) == 3:
        if stk[1] == '=':
            stk[0] = GetAtom(stk[2])
        elif stk[1] == '~':
            stk[0] = NotAtom(stk[2])
        elif stk[1] == '^':
            if stk[2].startswith('"'):
                stk[0] = MatchLex(stk[2][1:-1], quoted=True)
            else:
                stk[0] = MatchLex(stk[2])
    elif len(stk) == 4:
        stk[0] = StoreAtom(stk[1], stk[3])
    
def p_atom(stk):
    '''
    atom : ATOM
    '''
    stk[0] = Atom(stk[1])

def p_quoted(stk):
    '''
    quoted : QUOTED
    '''
    stk[0] = Atom(stk[1][1:-1])

def p_regex(stk):
    '''
    regex : REGEX
    '''
    # Extract the regex between the slash delimiters
    stk[0] = RE(stk[1][1:-1])

def p_star(stk):
    '''
    star : STAR
    '''
    stk[0] = All()

