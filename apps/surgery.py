from __future__ import with_statement
import sys, os, re
from optparse import OptionParser

from munge.cats.parse import parse_category
from munge.util.func_utils import compose

from apps.proxy_io import *
from munge.io.guess_ptb import PTBGuesser
from munge.io.guess import GuessReader
from munge.trees.traverse import *

from munge.util.iter_utils import flatten

class SurgeryException(Exception): pass

def load_trees(base, sec, doc, extension, guessers):
    path = os.path.join(base, "%02d" % sec, "wsj_%02d%02d.%s" % (sec, doc, extension))
    reader = GuessReader(path, guessers)
    return reader
    
def check_index(kid_list, locator):
    '''Checks that the given locator is a valid index into the child
list. Negative indices are permitted with the same semantics as list
indexing.'''
    if (not (-len(kid_list) <= locator < len(kid_list))) and locator != 'e':
        raise RuntimeError, "Child index %s out of bounds. Kids are %s" % (locator, kid_list)
    
def process(deriv, locator, instr):
    '''Processes one script instruction, given the derivation on which it is to operate, a locator string
identifying a node as the focus of the operation, and the instruction itself.'''
    locator = locator[:] # make a copy
    last_locator = locator.pop()
    
    cur_node = deriv

    for kid_index in locator:
        check_index(cur_node.kids, kid_index)
        cur_node = cur_node.kids[kid_index]
    
    check_index(cur_node.kids, last_locator)
    print "Locator names leaf %s" % cur_node.kids[last_locator]
    
    if instr == "d":
        # TODO: handle deleting the last kid, have to recursively delete. but PTB nodes have no parent ptr
        # otherwise assume this won't be done.
        # or we can have a node with empty kids yield an empty string representation
        del cur_node.kids[last_locator]
    elif instr.startswith("l"):
        # Sets the lexical item of a PTB node or CCGbank node.
        _, new_lex = instr.split('=')
        cur_node.kids[last_locator].lex = new_lex
    elif instr.startswith("t"):
        # Sets the POS tag of a PTB node.
        _, new_tag = instr.split('=')
        cur_node.kids[last_locator].tag = new_tag
    elif instr.startswith("c"):
        # Sets the category of a CCGbank node.
        _, new_cat = instr.split('=')
        cur_node.kids[last_locator].cat = parse_category(new_cat)
    elif instr.startswith("C"):
        _, new_bits = instr.split('=')
        cat, pos1, pos2, lex, catfix = new_bits.split(',')
        
        for attr in ('cat', 'pos1', 'pos2', 'lex', 'catfix'):
            value = locals()[attr]
            if value: # empty value for a field means do not change the field's value
                setattr(cur_node.kids[last_locator], attr, value)
    elif instr.startswith("i"):
        # Insert PTB leaf node.
        _, tag_and_lex = instr.split('=')
        tag, lex = tag_and_lex.split('|')

        new_leaf = penn.Leaf(tag, lex)
        if last_locator == 'e':
            cur_node.kids.append(new_leaf)
        else:
            cur_node.kids.insert(last_locator, new_leaf)
    elif instr.startswith('P') or instr.startswith('A'):
        # Prepend or append CCGbank absorption leaf node. Instruction is of the form 
        # I=leaf_cat|leaf_pos1|leaf_lex|leaf_catfix|parent_cat
        # If you leave out parent_cat then absorption is assumed.
        prepend = instr.startswith('P')
        
        _, commalist = instr.split('=')
        cat, pos1, lex, catfix, parent_cat = commalist.split('|')
        cat = parse_category(cat)
        
        new_leaf = ccg.Leaf(cat, pos1, pos1, lex, catfix) # No parent
        # node_prepend and append return None if no new root was installed, or the new root otherwise
        if prepend:
            maybe_new_root = node_prepend(cur_node.kids[last_locator], new_leaf, parent_cat or cur_node.kids[last_locator].cat)
        else:
            maybe_new_root = node_append(cur_node.kids[last_locator], new_leaf, parent_cat or cur_node.kids[last_locator].cat)
    
        # Install a new root if one was created
        if maybe_new_root:
            deriv = maybe_new_root
            
    elif instr.startswith('S'): # Shrink absorption
        focus = cur_node.kids[last_locator]
        if focus.lch.is_leaf() and focus.rch.cat == focus.cat:
            maybe_new_root = shrink(focus, left_is_leaf=True)
        elif focus.rch.is_leaf() and focus.lch.cat == focus.cat:
            maybe_new_root = shrink(focus, left_is_leaf=False)
        else:
            raise SurgeryException("The focused node must be an instance of absorption (X T -> T or T X -> T).")
            
        if maybe_new_root:
            deriv = maybe_new_root

    return deriv
    
def shrink(focus, left_is_leaf=True):
    if focus.parent is not None:
        # XXX: since nodes in this tree are CCGbankNodeProxy objects, they don't pass an identity check with the child as accessed through the parent
        # even after making CCGbankNodeProxy.parent() return a proxy-wrapped node, it doesn't pass an identity check. We can't override the identity
        # check so we need to do a deep comparison
        was_left_child = focus.parent.lch == focus
                
        if was_left_child:
            if left_is_leaf:
                focus.parent.lch = focus.rch
            else:
                focus.parent.lch = focus.lch
        else:
            if left_is_leaf:
                focus.parent.rch = focus.rch
            else:
                focus.parent.rch = focus.lch
                
        return None
                
    else:
        return focus.rch if left_is_leaf else focus.lch

def write_doc(outdir, extension, sec, doc, bundles):
    '''Writes a given document back to disk.'''
    tree_path = os.path.join(outdir, "%02d" % sec)
    tree_file = os.path.join(tree_path, "wsj_%02d%02d.%s" % (sec, doc, extension))
    if not os.path.exists(tree_path): os.makedirs(tree_path)

    with file(tree_file, 'w') as f:
        print >>f, str(bundles)

parser = OptionParser(conflict_handler='resolve')
parser.set_defaults(format='ptb')

parser.add_option('-i', '--input', help='Path to input directory (usually AUTO/ or wsj/)', dest='base')
parser.add_option('-o', '--output', help='Output directory. Only changed files will be output', dest='out')
parser.add_option('-f', '--format', help='Input format (ccg|ptb), default ptb', dest='format')

opts, remaining_args = parser.parse_args(sys.argv)
parser.destroy()

if not (opts.base and opts.out):
    print "Give options -i (--input) and -o (--output)."
    sys.exit(1)
    
guessers_to_use = (ProxyWritableCCGbankGuesser, PTBGuesser)

if opts.format == 'ccg':
    extension = 'auto'
elif opts.format == 'ptb':
    extension = 'mrg'
else:
    print "Invalid format %s given." % opts.format
    sys.exit(2)

base = opts.base
spec_re = re.compile(r'(\d+):(\d+)\((\d+)\)')

reading_spec = True
cur_trees = None
cur_tree = None

changes = {}

def maybe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError): return value
    
def get_locator_sequence_to(leaf):
    ret = []
    cur = leaf
    while cur.parent is not None:
        ret.append(0 if cur.parent.lch == cur else 1) # see shrink for reason why deep comparison is being done
        cur = cur.parent
    return list(reversed(ret))
    
def desugar(value, last_locator_bits, deriv):
    '''Lets the user use "l" or "r" in the locator path to mean children 0 or 1 (of a CCGbank derivation).'''
    if value == 'l': return 0
    elif value == 'r': return 1
    elif value == '_': 
        if last_locator_bits is None:
            raise SurgeryException('_ not bound to a value (is this the first script command?)')
        return last_locator_bits
    elif value == '@':
        if last_locator_bits is None:
            raise SurgeryException('@ depends on _, which is not yet bound to a value')
        insert_locator = list(last_locator_bits)
        print "last locator bits:", last_locator_bits
        while insert_locator and insert_locator[-1] in ('l', 0):
            del insert_locator[-1]
         
        insert_locator[-1] = 0

        print "using insert locator", insert_locator
        return insert_locator
    elif value.startswith('$'): # return _parent_ of requested leaf
        leaf_index = int(value[1:])
        requested_leaf = get_leaf(deriv, leaf_index)
        locator_to_requested_leaf = get_locator_sequence_to(requested_leaf)
        print "ltl:", locator_to_requested_leaf
        return locator_to_requested_leaf[:-1]
        
    else: return value

# cache the last locator sequence so it can be referred to quickly
last_locator_bits = None

for line in sys.stdin.readlines():
    print line
    if line[0] == '#': continue
    
    matches = spec_re.match(line)
        
    if matches and len(matches.groups()) == 3:
        sec, doc, deriv = map(int, matches.groups())
        
        if (sec, doc) not in changes:
            changes[ (sec, doc) ] = load_trees(base, sec, doc, extension, guessers_to_use)
            
        cur_tree = changes[ (sec, doc) ][deriv]
        
    else:
        line = line.rstrip()
        print line

        locator, instr = line.split(' ', 2)
        print "raw locator:",locator
        locator_bits = list(flatten(map(compose(maybe_int, lambda value: desugar(value, last_locator_bits, cur_tree.derivation)), locator.split(';'))))
        print "real locator:",locator_bits
        last_locator_bits = locator_bits
        print "setting llb:",locator_bits
        
        changes[ (sec, doc) ][deriv].derivation = process(cur_tree.derivation, locator_bits, instr)
        print
        print changes[ (sec, doc) ][deriv].derivation
        
# Write out aggregated changes
for ((sec, doc), bundle) in changes.iteritems():
    write_doc(opts.out, extension, sec, doc, bundle)
