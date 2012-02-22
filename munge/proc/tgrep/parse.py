# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

try:
    import ply.lex as lex
    import ply.yacc as yacc
except ImportError:
    import lex, yacc

import munge.ccg.nodes as ccg
from munge.cats.cat_defs import C
from munge.util.err_utils import warn, err
from munge.proc.tgrep.nodes import *
from munge.util.exceptions import TgrepException

tokens = ("LPAREN", "RPAREN", "ATOM", "REGEX", "REGEX_SPEC", "OP", "UNARY_OP", "QUESTION",
          "QUOTED", "PIPE", "BANG", "LT", "GT", "EQUAL", "STAR", "TILDE", "CARET", "AT")

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
    
def t_TILDE(t):
    r'~'
    return t

# Assume no whitespace is permitted within a regex.
def t_REGEX(t):
    r'/([^/\s]|\/)+/'
    return t
    
# TODO: There's a bug with REGEX_SPEC; if the input is "a" then it gets lexed as REGEX_SPEC
#       Need to make REGEX_SPEC part of the definition of the REGEX token
def t_REGEX_SPEC(t):
    r'[a]'
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
    
def t_QUESTION(t):
    r'\?'
    return t
    
def t_AT(t):
    r'@'
    return t

# Productions need to be sorted by descending length (maximal munch)
def t_OP(t):
    r'(<<(,|\#)?|>>\'?|<%|<\#|(<(-?\d*))|>|\.\.?|\$\.?\.?|&)'
    return t
    
def t_STAR(t):
    r'\*'
    return t
    
def t_UNARY_OP(t):
    r'(\#<\d+)'
    return t

def t_ATOM(t):
    r'''[^/\\"\s{=][^\s]+[^/\\"\s}=]|[^/\\\s{=][^/\\\s}=]|[^/\\\s{}=]'''
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
               | unary_op
               | op matcher
               | BANG constraint
               | QUESTION constraint
               | constraint PIPE constraint
    '''
    if len(stk) == 2:
        stk[0] = stk[1]
    elif len(stk) == 3:
        if stk[1] == '!':
            stk[0] = Negation(stk[2])
        elif stk[1] == '?':
            stk[0] = Reluctant(stk[2])
        else:
            stk[0] = Constraint(stk[1], stk[2])
            
    elif len(stk) == 4:
        stk[0] = Alternation(stk[1], stk[3])
        
def p_unary_op(stk):
    '''
    unary_op : UNARY_OP
    '''
    stk[0] = Constraint(stk[1])

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
            | CARET full_regex
            | AT ATOM
            | AT QUOTED
            | AT full_regex
    '''
    if len(stk) == 2:
        stk[0] = stk[1]
    elif len(stk) == 3:
        if stk[1] == '=':
            stk[0] = GetAtom(stk[2])
        elif stk[1] == '~':
            stk[0] = NotAtom(stk[2])
        elif stk[1] == '^':
            if isinstance(stk[2], tuple):
                stk[0] = RELex(*stk[2])
                
            elif stk[2].startswith('"'):
                stk[0] = MatchLex(stk[2][1:-1], quoted=True)
            else:
                stk[0] = MatchLex(stk[2])
        elif stk[1] == '@':
            # TODO: refactor this with above
            if isinstance(stk[2], tuple):
                stk[0] = RECat(*stk[2])
                
            elif stk[2].startswith('"'):
                stk[0] = MatchCat(stk[2][1:-1], quoted=True)
            else:
                stk[0] = MatchCat(stk[2])
                
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
    regex : full_regex
    '''
    stk[0] = RE(*stk[1])
    
def p_full_regex(stk):
    # unlike the other productions, this returns a tuple of arguments to be splatted and
    # passed to a regex-taking node type (RE or REValue)
    '''
    full_regex : REGEX
               | REGEX REGEX_SPEC
    '''
    # Extract the regex between the slash delimiters
    if len(stk) == 2:
        stk[0] = (stk[1][1:-1], True) # anchor_at_start = True
    elif len(stk) == 3:
        spec = stk[2]
        if spec == 'a':
            stk[0] = (stk[1][1:-1], False) # anchor_at_start = False
        else:
            err('Invalid regex specifier %s.', spec)

def p_star(stk):
    '''
    star : STAR
    '''
    stk[0] = All()

