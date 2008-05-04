from __future__ import with_statement
import sys, os, re
from munge.penn.io import PTBReader
from munge.penn.nodes import *
from optparse import OptionParser

def load_trees(base, sec, doc):
    path = os.path.join(base, "%02d" % sec, "wsj_%02d%02d.mrg" % (sec, doc))
    reader = PTBReader(path)
    return reader
    
def process(deriv, locator, instr):
    last_locator = locator.pop()
    
    cur_node = deriv
    for kid_index in locator:
        cur_node = cur_node.kids[kid_index]
        
    if instr == "d":
        # TODO: handle deleting the last kid, have to recursively delete. but PTB nodes have no parent ptr
        # otherwise assume this won't be done.
        # or we can have a node with empty kids yield an empty string representation
        del cur_node.kids[last_locator]
    elif instr.startswith("l"):
        _, new_lex = instr.split('=')
        cur_node.kids[last_locator].lex = new_lex
    elif instr.startswith("t"):
        _, new_tag = instr.split('=')
        cur_node.kids[last_locator].tag = new_tag
    elif instr.startswith("i"):
        _, tag_and_lex = instr.split('=')
        tag, lex = tag_and_lex.split('|')

        new_leaf = Leaf(tag, lex)
        if last_locator == 'e':
            cur_node.kids.append(new_leaf)
        else:
            cur_node.kids.insert(last_locator, new_leaf)

    return deriv

#    print deriv

def write_doc(outdir, sec, doc, trees):
    tree_path = os.path.join(outdir, "%02d" % sec)
    tree_file = os.path.join(tree_path, "wsj_%02d%02d.mrg" % (sec, doc))
    if not os.path.exists(tree_path): os.makedirs(tree_path)

    with file(tree_file, 'w') as f:
        print >>f, "\n".join("(%s)" % str(tree) for tree in trees)

parser = OptionParser(conflict_handler='resolve')
parser.add_option('-i', '--ptb-base', help='Path to wsj/ directory', dest='base')
parser.add_option('-o', '--output', help='Output directory. Only changed files will be output', dest='out')

opts, remaining_args = parser.parse_args(sys.argv)
parser.destroy()

base = opts.base
spec_re = re.compile(r'(\d+):(\d+)\((\d+)\)')

reading_spec = True
cur_trees = None
cur_tree = None

changes = {}

def maybe_int(value):
    try:
        return int(value)
    except ValueError: return value

for line in sys.stdin.readlines():
    matches = spec_re.match(line)
        
    if matches and len(matches.groups()) == 3:
        sec, doc, deriv = map(maybe_int, matches.groups())
        
        #cur_trees = load_trees(base, sec, doc)
        if (sec, doc) not in changes:
            changes[ (sec, doc) ] = load_trees(base, sec, doc)
        #cur_tree = cur_trees[deriv]
        cur_tree = changes[ (sec, doc) ][deriv]
        
    else:
        line = line.rstrip()
        locator, instr = line.split(' ')
        locator_bits = map(maybe_int, locator.split(';'))
        #cur_trees[deriv] = process(cur_tree, locator_bits, instr)
        changes[ (sec, doc) ][deriv] = process(cur_tree, locator_bits, instr)
        # this means you can only write to a document once
        # we need to gather all changes to a given document and write only after each document
        #write_doc(opts.out, sec, doc, deriv, cur_trees.derivs)

print changes
for ((sec, doc), deriv) in changes.iteritems():
    write_doc(opts.out, sec, doc, deriv.derivs)
