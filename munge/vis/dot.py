from __future__ import with_statement
from string import Template
from munge.util.err_utils import warn, err
import re, os
from subprocess import Popen, PIPE

id = 0
def get_id():
    '''Gets a unique ID identifying a DOT node.'''
    global id

    ret = "n%d" % id
    id += 1
    return ret

def make_derivation(deriv, assigned_id=None):
    '''Generates the body of the DOT representation.'''
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
    '''Generates the DOT representation.'''
    return '''digraph G {\n%s}''' % make_derivation(deriv)

def write_graph(deriv, fn):
    '''Writes the DOT representation to a file.'''
    with open(fn, 'w') as f:
        f.write(make_graph(deriv))

def write_png(deriv, fn):
    cin = cout = None
    try:
        dot_path = os.popen('which dot').read().strip()
        if not dot_path:
            err('dot not found on this system. Ensure that dot is in the PATH.')
            return
            
        cmd = '%s -Tpng -o %s 2>/dev/null' % (dot_path, fn)
        pipes = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
        
        cin, cout = pipes.stdin, pipes.stdout
        cin.write(make_graph(deriv))
        
        if pipes.returncode is not None and pipes.returncode != 0:
            raise RuntimeError('dot terminated with non-zero return code: %d' % pipes.returncode)

    finally:
        if cin:  cin.close()
        if cout: cout.close()
