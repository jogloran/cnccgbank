# coding: utf-8
# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import re
import os
import sys
import envoy
import traceback
from munge.io.guess import GuessReader
from apps.cn.mkdeps import mkdeps, UnificationException
from apps.cn.mkmarked import naive_label_derivation
from munge.trees.traverse import leaves

matched = unmatched = 0
munge_error_sents = 0
dep_error_sents = 0
skipped_sents = 0
total_sents = 0

anno_fn = sys.argv[1]
anno = file(anno_fn, 'r')

def deriv_id_to_components(deriv_id):
    m = re.match(r'(\d+):(\d+)\((\d+)\)', deriv_id)
    if m:
        return map(int, m.groups())
    raise Exception, "Invalid deriv_id: %s" % deriv_id

def deriv_id_to_filespec(deriv_id, with_deriv=True, with_section_dir=True):
    sec, doc, deriv = deriv_id_to_components(deriv_id)
    if with_deriv:
        if with_section_dir: 
            return os.path.join('%02d'%sec, 'chtb_%02d%02d.fid:%d'%(sec,doc,deriv))
        else:
            return "chtb_%02d%02d.fid:%d" % (sec, doc, deriv)
    else:
        if with_section_dir:
            return os.path.join('%02d'%sec, 'chtb_%02d%02d.fid'%(sec,doc))
        else:
            return "chtb_%02d%02d.fid" % (sec, doc)

def remap_indices(head_index, arg_index, deriv_id):
    remapper = remappers[deriv_id]
    return remapper[head_index], remapper[arg_index]

def remapper(leaves):
    def is_trace(leaf):
        return leaf.lex.startswith('*')

    #print ' '.join(l.tag for l in leaves)
    last, cur = None, None
    target_index = -1
    result = []

    found = False
    for leaf in leaves:
        last, cur = cur, leaf

        is_first_kid = (leaf.parent is not None) and (leaf.parent[0] is leaf)

        if is_trace(leaf):
            result.append(None)
        elif (last is not None and (
              (last.tag in ('VV','VA') and last.tag == cur.tag and cur.parent.tag == 'VCD') or
              (not is_first_kid and cur.parent.tag == 'VPT'))):
            result.append(target_index)
        else:
            target_index += 1
            result.append(target_index)

    return result

def get_remapper_for(deriv_id):
    filespec = deriv_id_to_filespec(deriv_id, with_section_dir=False)
    reader = GuessReader( os.path.join('cn', filespec) )
    bundle = iter(reader).next()
    root = bundle.derivation
    return remapper(leaves(root))

if len(sys.argv) > 2:
    data_dir = sys.argv[2]
    made_docs = os.path.join(data_dir, 'AUTO')
    using_data_dir = True
else:
    made_docs = 'fixed_np'
    using_data_dir = False
print made_docs

# make all the documents mentioned in the anno file (first column)
docs_to_make = set( line.split(' ')[0] for line in open(anno_fn, 'r').xreadlines() )
remappers = {}
for deriv_id in docs_to_make:
    remappers[ deriv_id ] = get_remapper_for(deriv_id)

    if os.path.isfile(os.path.join(made_docs, deriv_id_to_filespec(deriv_id, with_deriv=False, with_section_dir=using_data_dir))):
        continue

    if not using_data_dir:
        result = envoy.run('./make_all.sh %s' % deriv_id_to_filespec(deriv_id, with_deriv=False, with_section_dir=False))
        if result.status_code != 0:
            print "Failed to make %s" % deriv_id

nsents = len(docs_to_make)
bad_sents = set()

for line in anno:
    line = line.rstrip()

    deriv_id, head_index, arg_index, nld_type = line.split(' ', 4)
    head_index = int(head_index)
    arg_index = int(arg_index)

    sec, doc, deriv_no = deriv_id_to_components(deriv_id)

    # read in the derivation
    if using_data_dir:
        reader = GuessReader(os.path.join(made_docs, deriv_id_to_filespec(deriv_id, with_deriv=True, with_section_dir=True)))
    else:
        reader = GuessReader(os.path.join('final', deriv_id_to_filespec(deriv_id, with_deriv=True, with_section_dir=True)))
    try:
        bundle = iter(reader).next()
        total_sents += 1

        root = bundle.derivation
        # run mkmarked on the derivation
        root = naive_label_derivation(root)
        def extract_index(s):
            return int(s.split('`')[1])
        # run mkdeps on the derivation
        try:
            deps = mkdeps(root, postprocessor=extract_index)
        except UnificationException:
            print "mkdeps failed on %s" % deriv_id
            traceback.print_exc(file=sys.stdout)
            deps = None

        def deps_match(head_index, arg_index, dep):
            return head_index==dep[0] and arg_index==dep[1]

        if deps:
            sys.stdout.write('%d %d -> ' % (head_index, arg_index))
            try:
                anno_head_index, anno_arg_index = remap_indices(head_index, arg_index, deriv_id)

                print 'annotator: %d %d' % (anno_head_index, anno_arg_index)

                if any( deps_match(anno_head_index, anno_arg_index, dep) for dep in deps ):
                    matched += 1
                else:
                    print "%d %d missing from mkdeps in %s" % (anno_head_index, anno_arg_index, deriv_id)
                    for a,b,c,d in deps:
                        print a,b
                    bad_sents.add(deriv_id)
                    unmatched += 1
            except Exception, e:
                skipped_sents += 1
                bad_sents.add(deriv_id)
                print 'skipping %s' % deriv_id
                print 'remapper:', remappers[deriv_id]
                print 'exception:'
                traceback.print_exc(file=sys.stdout)
                continue
        else: # mkdeps problem
            dep_error_sents += 1
            bad_sents.add(deriv_id)
            
    except StopIteration:
        munge_error_sents += 1
        print "not made: %s" % deriv_id

print 'dependencies preserved: %d/%d=%.2f%%' % (matched, unmatched+matched, matched/float(unmatched+matched)*100.)
print 'munge errors: %2d/% 3d=%.2f%% of deps' % (munge_error_sents, total_sents, munge_error_sents/float(total_sents)*100.)
print 'dep errors:   %2d/% 3d=%.2f%% of deps' % (dep_error_sents, total_sents, dep_error_sents/float(total_sents)*100.)
print 'skipped:      %2d/% 3d=%.2f%% of deps' % (skipped_sents, total_sents, skipped_sents/float(total_sents)*100.)

print
nbad_sents = len(bad_sents)
print 'annotated sents with problems: %2d/% 3d=%.2f%%' % (nbad_sents, nsents, nbad_sents/float(nsents)*100.)
