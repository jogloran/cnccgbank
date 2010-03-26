from __future__ import with_statement
from string import Template
from munge.util.err_utils import warn, err
import re, os
from subprocess import Popen, PIPE
import munge.ccg.nodes as ccg
from munge.cats.trace import analyse

id = 0
def get_id():
    '''Gets a unique ID identifying a DOT node.'''
    global id

    ret = "n%d" % id
    id += 1
    return ret
    
Abbreviations = {
    "fwd_raise": ">T",
    "bwd_raise": "<T",
    "fwd_comp": ">B",
    "fwd_xcomp": ">Bx",
    "bwd_comp": "<B",
    "bwd_xcomp": "<Bx",
    "fwd_subst": ">S",
    "fwd_xsubst": ">Sx",
    "bwd_subst": "<B",
    "bwd_xsubst": "<Bx"
}

def make_derivation(deriv, assigned_id=None):
    '''Generates the body of the DOT representation.'''
    
    if deriv.is_leaf():
        return '''%s [shape="none",height=0.17,label="%s"]\n''' % (assigned_id, deriv.label_text())
        
    else:
        ret = []
        root_id = assigned_id or get_id()

        for child in deriv:
            child_id = get_id()

            if isinstance(deriv, (ccg.Leaf, ccg.Node)):
                comb_name = re.escape(Abbreviations.get(analyse(deriv.lch.cat, deriv.rch and deriv.rch.cat, deriv.cat), ''))
                
                if comb_name:
                    shape_type = "record"
                    label_text = "<o>%s|%s" % (deriv.label_text(), comb_name)
                else:
                    shape_type = "box"
                    label_text = deriv.label_text()
                    
                ret.append('''%s [shape="%s",height=0.1,label="%s"]\n''' % (root_id, shape_type, label_text))
                ret.append("%s:o -> %s:o\n" % (root_id, child_id))
                ret.append(make_derivation(child, child_id))
                
            else:
                ret.append('''%s [shape="box",height=0.1,label="%s"]\n''' % (root_id, deriv.label_text()))
                ret.append("%s -> %s\n" % (root_id, child_id)) 
                ret.append(make_derivation(child, child_id))

        return ''.join(ret)

def make_graph(deriv, label=""):
    '''Generates the DOT representation.'''
    # TODO: Need to get rid of the font change at some point
    return (
'''digraph G {
node [fontname=Hei]
label="%s"
labelloc="t"
labeljust="r"
fontname="Helvetica"
fontsize=16
%s}''' % (label, make_derivation(deriv)))

def write_graph(deriv, fn, label=""):
    '''Writes the DOT representation to a file.'''
    with open(fn, 'w') as f:
        t = unicode(make_graph(deriv, label=label), 'utf-8')
        f.write(t.encode('utf-8'))

def write_png(deriv, fn, label=""):
    return write_dot_format(deriv, fn, "png", label=label)

def write_pdf(deriv, fn, label=""):
    return write_dot_format(deriv, fn, "pdf", label=label)

dot_path = None
def write_dot_format(deriv, fn, format, label=""):
    cin = cout = None
    try:
        global dot_path
        if not dot_path:
            dot_path = os.popen('which dot').read().strip()
            if not dot_path:
                err('dot not found on this system. Ensure that dot is in the PATH.')
                return
            
        cmd = '%s -T%s -o %s 2>/dev/null' % (dot_path, format, fn)
        pipes = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
        
        cin, cout = pipes.stdin, pipes.stdout
        cin.write(make_graph(deriv, label=label)); cin.close()
        
        pipes.wait()
        if pipes.returncode is not None and pipes.returncode != 0:
            raise RuntimeError('dot terminated with non-zero return code: %d' % pipes.returncode)

    finally:
        if cin:  cin.close()
        if cout: cout.close()
        
if __name__ == '__main__':
    from munge.penn.parse import parse_tree
    import sys
    
    print make_graph(parse_tree(sys.stdin.read())[0])
