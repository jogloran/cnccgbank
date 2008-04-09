from __future__ import with_statement
from string import Template
import re

id = 0
def get_id():
    global id

    ret = "n%d" % id
    id += 1
    return ret

def make_derivation(deriv, assigned_id=None):
    if deriv.is_leaf():
        return '''%s [shape="none",height=0.17,label="%s"]\n''' % (assigned_id, deriv.label_text())
        
    else:
        ret = []
        root_id = assigned_id or get_id()

        for child in deriv:
            child_id = get_id()

            ret.append('''%s [shape="record", height=0.1,label="%s"]\n''' % (root_id, deriv.label_text()))
            ret.append("%s:o -> %s:o\n" % (root_id, child_id)) 
            # TODO: Work out how to add combinator annotation without making this ccg derivation-specific
            ret.append(make_derivation(child, child_id))

        return ''.join(ret)

def make_graph(deriv):
    return '''digraph G {\n%s}''' % make_derivation(deriv)

def write_graph(deriv, fn):
    with open(fn, 'w') as f:
        f.write(make_graph(deriv))
