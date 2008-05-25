import ply.lex as lex
import ply.yacc as yacc
import sys, re

import munge.ccg.nodes as ccg
from munge.cats.cat_defs import C
from munge.util.err_utils import warn, err
from munge.proc.tgrep.nodes import *

tokens = ("LPAREN", "RPAREN", "ATOM", "OP", "REGEX", "QUOTED")

t_REGEX = r'/([^/\s]|\/)+/'
# This is pretty hacky. We rely on the fact that / or \ are never valid categories
# and neither are [/\]X or X[/\] for any X, letting us distinguish between a valid
# category and a regex. Assume no whitespace is permitted within categories.

# TODO: This doesn't include punctuation yet. Do a quick run over the treebank to see
# what characters are valid in category names. Not to mention modes
#t_ATOM = r'[\w\d_\[\]()][[\w\d_\[\]()/\\.]+[\w\d_\[\]()]|[\w\d_\[\]()]{2}|[\w\d_\[\]()]+'
t_ATOM = r'[^/\\"{}][^\s]+[^/\\"{}]|[^/\\"{}]{1,2}'
t_QUOTED = r'"[^"]+"'

t_ignore = ' \t\r\v\f\n'
    
# Productions need to be sorted by descending length (maximal munch)
t_OP = r'!?(<<,?|>>\'?|(<-?\d?)|>|\.\.?|\$\.?\.?)'
t_LPAREN = r'\{'
t_RPAREN = r'\}'

def t_error(t):
    warn("Illegal character `%s' encountered.", t.value[0])
    t.lexer.skip(1)
    
def p_error(stk):
    err("Syntax error encountered.")
        
def p_node(stk):
    '''
    node : matcher
         | node constraint_list
         | group
    '''
    if len(stk) == 2:
        stk[0] = Node(stk[1])
    elif len(stk) == 3:
        stk[0] = stk[1]#Node(stk[1])
        stk[0].constraints.extend(stk[2])
    elif len(stk) == 4:
        stk[0] = stk[1]
            
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
    constraint : OP matcher
               | OP LPAREN node RPAREN
    '''
    if len(stk) == 3:
        stk[0] = Constraint(stk[1], stk[2])
    elif len(stk) == 5:
        stk[0] = Constraint(stk[1], Group(stk[3]))
        
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
    '''
    stk[0] = stk[1]
    
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
