from __future__ import with_statement
import sys, re, os

from optparse import OptionParser
from glob import glob

from munge.util.err_utils import warn, info, err

from munge.quote.span import SpanQuoter
from munge.quote.shift import ShiftComma
from munge.quote.swap import SwapComma

from munge.penn.io import PTBReader
from munge.ccg.io import CCGbankReader
from munge.ccg.deps_io import CCGbankDepsReader

from munge.trees.traverse import text, text_without_quotes_or_traces, text_without_traces

DefaultLogFile = "quote_error"

def register_builtin_switches(parser):
    parser.set_defaults(punct_method="shift",
                        quote_method="span",
                        quotes="both",
                        higher="left",
                        quiet=False,
                        log=True,
                        logfile=DefaultLogFile)
                        
    parser.add_option("-i", "--penn-in", help="Path to wsj/ directory", action="store",
                      dest="penn_in", metavar="DIR")
    parser.add_option("-I", "--ccgbank-in", help="Path to CCGbank AUTO/ and PARG/ directory", action="store",
                      dest="ccg_in", metavar="DIR")
    parser.add_option("-o", "--output", help="Output directory for quoted data", dest="outdir", metavar="DIR"),
    parser.add_option("-p", "--punct-method", choices=('none', 'swap', 'shift'),
                      help="Algorithm for handling absorbed punctuation (none|swap|shift)",
                      dest="punct_method", metavar='ALGO')
    parser.add_option("-Q", "--quote-method", choices=('span', 'lca'),
                      help="Algorithm for inserting quotes (span|lca)",
                      dest="quote_method", metavar='ALGO')
    parser.add_option("-d", "--insert", choices=('both', 'left', 'right'),
                      help="Which quotes to reinsert (both|left|right)",
                      dest="quotes", metavar='DIR')
    parser.add_option("-H", "--higher", choices=('left', 'right'),
                      help="Which of the opening (left) or closing (right) quote is the higher in the resulting tree",
                      dest="higher", metavar='DIR')
    parser.add_option("--log", help="Log derivations which cause problems to a file", dest="logfile", metavar="FILE")
    parser.add_option("-q", "--quiet", help="Produce less output", action="store_true", dest="quiet")
    
# required_args maps the name of the 'dest' variable of each required option to a summary of its switches (this text is
# shown to the user)
required_args = {
    "penn_in": "-i (--penn-in)",
    "ccg_in" : "-I (--ccgbank-in)",
    "outdir" : "-o (--output)"
}
def check_for_required_args(opts):
    '''Ensures that the required arguments are all present, and notifies the user as to which of them are not.'''
    arg_missing = False
    for (required_arg, arg_switches) in required_args.iteritems():
        if getattr(opts, required_arg, None) is None:
            err("Argument %s is mandatory.", arg_switches)
            arg_missing = True

    if arg_missing:
        sys.exit(1)
            
def fix_secdoc_string(secdoc):
    '''Given a section/document specifier of the form S:D, where S or D may be absent, returns a specifier string
with S and D padded by a zero to 2 digits if necessary, or with an absent S or D component replaced by an asterisk.'''
    if secdoc is None:
        return '*'
    if len(secdoc) == 1:
        return '0' + secdoc
    return secdoc
    
deriv_re = re.compile(r'([*\d]+)?:([*\d]+)?')
def parse_requested_derivs(args):
    '''Makes each section/document specifier canonical using fix_secdoc_string.'''
    result = []
    
    for arg in args:
        match = deriv_re.match(arg)
        if match and len(match.groups()) == 2:
            sec, doc = map(fix_secdoc_string, match.groups())
            
            result.append( (sec, doc) )
            
    return result

def match_trees(penn_trees, ccg_trees):
    '''Given two lists, of PTB and CCGbank trees which we believe to belong to the same document file, this removes
those PTB trees which do not correspond to any CCGbank tree.'''
    cur_ptb_index = 0
    result = []
    
    for ccg_bundle in ccg_trees:
        ccg_tree_matched = False
        
        while not ccg_tree_matched:
            if cur_ptb_index >= len(penn_trees): break
        
            ccg_text = text(ccg_bundle.derivation)
            ptb_text = text_without_quotes_or_traces(penn_trees[cur_ptb_index].derivation)
        
            if ptb_text != ccg_text:
                warn("In document %s:", ccg_bundle.label())
                warn("\tCCG tokens: %s", ' '.join(ccg_text))
                warn("\tPTB tokens: %s", ' '.join(ptb_text))
                pass
            else:
                result.append( penn_trees[cur_ptb_index] )
                ccg_tree_matched = True
            
            cur_ptb_index += 1
            
    return result
            
from munge.util.list_utils import first_index_such_that, last_index_such_that
from munge.trees.traverse import is_ignored, leaves
from itertools import izip, count
def spans(ptb_tree):
    '''Returns a sequence of tuples (B, E), where the Bth token from the start, and the Eth token from the end
of the given PTB derivation span a quoted portion of the text.'''
    
    #  # This is implemented as returning a sequence for generality: our naive implementation only ever locates a
    #     # single (outermost) span of quoted text, so this implementation only ever returns a sequence of at most one
    #     # tuple. A smarter implementation would handle and identify nested quotes, as well as multiple spans.
    # 
    #     leaf_nodes = [leaf for leaf in leaves(ptb_tree) if not is_ignored(leaf, ignoring_quotes=False)]
    # 
    #     # TODO: This doesn't actually handle the case when you have `` ... `...' (s
    #     fi, li = (first_index_such_that(lambda node: node.tag == "``" and node.lex in ("``", "`"), leaf_nodes), 
    #           first_index_such_that(lambda node: node.tag == "''" and node.lex in ("''", "'"), reversed(leaf_nodes)))
    # 
    # #    if li is not None: li += 1
    #     yield (fi,li)
    leaf_nodes = [leaf for leaf in leaves(ptb_tree) if not is_ignored(leaf, ignoring_quotes=False)]
    # TODO: do this without incurring another full pass through the full nodes list
    leaf_nodes_without_quotes = [leaf for leaf in leaf_nodes if not is_ignored(leaf, ignoring_quotes=True)]
    leaf_count = len(leaf_nodes_without_quotes)
    
    result = []
    quote_stack = []
    index = 0
    for leaf in leaf_nodes:
        if leaf.lex in ("``", "`"):
            quote_stack.append( (leaf.lex, index) )
        elif leaf.tag != "POS" and leaf.lex in ("''", "'"):
            if quote_stack:
                open_quote, span_begin = quote_stack.pop()
                if (open_quote == "``" and leaf.lex != "''" or
                    open_quote == "`"  and leaf.lex != "'"):
                    warn("Unbalanced quotes, abandoning.")
                    break
                
                # we treat the span end index as leaf_count-index, not that minus one,
                # because when we encounter the close quote, we are already one index
                # past the end of the quoted span.
                result.append( (span_begin, leaf_count-index, open_quote) )
            else:
                if leaf.lex == "''":
                    quote_type = "``"
                elif leaf.lex == "'":
                    quote_type = "`"
                else:
                    err("spans: should not reach")
                    
                result.append( (None, leaf_count-index, quote_type) )
        else:
            index += 1
                
    while quote_stack:
        remaining_quote, span_begin = quote_stack.pop()
        if remaining_quote in ("``", "`"):
            result.append( (span_begin, None, remaining_quote) )
        else:
            warn("Unexpected quote %s after exhausting input.", remaining_quote)
            
    return result

           
def fix_dependency(dep, quote_index):
    '''Updates the dependency data to accommodate the insertion of a new leaf at a given index. This means that
every index to the right of the newly inserted node must be incremented.'''
    for dep_row in dep:
        if quote_index >= dep_row.fields[0]:
            dep_row.fields[0] += 1
        if quote_index >= dep_row.fields[1]:
            dep_row.fields[1] += 1
    
    return dep
           
def fix_dependencies(dep, quote_indices):
    '''Updates the dependency data to accommodate the insertion of an open and/or close quote node, given the indices
at which each occurs.'''
    open_quote_index, close_quote_index = quote_indices
    
    if open_quote_index:
        dep = fix_dependency(dep, open_quote_index)
        quote_indices = map(lambda e: e and e+1, quote_indices)
    if close_quote_index:
        dep = fix_dependency(dep, close_quote_index + 1)
        quote_indices = map(lambda e: e and e+1, quote_indices)
        
    return dep 
    
def fix_quote_spans(quote_spans, quote_indices):
    open_quote_index, close_quote_index = quote_indices
    
    inserted_quotes = 0
    if open_quote_index is not None:
        inserted_quotes += 1
    if close_quote_index is not None:
        inserted_quotes += 1
    
    # The adjustment is unnecessary for the end quote because we are adding quotes from left
    # to right, and the end quote indices are counted from the right end of the string.
    # This means that no addition of quotes starting from the left can affect an end quote
    # index.
    # We adjust every start index lying strictly to the right of the greater of the inserted
    # open quote index, by the number of quotes inserted.
    def _fix_quote_spans(bep):
        b, e, p = bep
        b_ = None if (b is None) else b
        
        if b is None:
            b_ = None
        else:
            b_ = b
            if b_ > open_quote_index:
                b_ += inserted_quotes
        
        return (b_, e, p)
        
    return map(_fix_quote_spans, quote_spans)

def process(ptb_file, ccg_file, deps_file, ccg_auto_out, ccg_parg_out, higher, quotes, quoter):
    '''Reinstates quotes given a PTB file and its corresponding CCGbank file and deps file.'''
    with file(ccg_auto_out, 'w') as ccg_out:
        with file(ccg_parg_out, 'w') as parg_out:
            penn_trees = list(PTBReader(ptb_file))
            ccg_trees  = list(CCGbankReader(ccg_file))
            deps       = list(CCGbankDepsReader(deps_file))
            
            matched_penn_trees = match_trees(penn_trees, ccg_trees)

            for (ptb_bundle, ccg_bundle, dep) in zip(matched_penn_trees, ccg_trees, deps):
                ptb_tree, ccg_tree = ptb_bundle.derivation, ccg_bundle.derivation

                quote_spans = spans(ptb_tree)
                while quote_spans:
                    print quote_spans
                    v = quote_spans.pop(0)
                    print v
                    span_start, span_end, quote_type = v
                    if span_start is None and span_end is None: continue
                    
                    info("Reinstating quotes to %s (%s, %s)", ccg_bundle.label(), span_start, span_end)
                    
                    ccg_tree, quote_indices = quoter.attach_quotes(ccg_tree, span_start, span_end, quote_type, higher, quotes)
                    # In case a new root has been installed, re-assign the new root to the CCGbank bundle
                    ccg_bundle.derivation = ccg_tree
                    
                    # Shift remaining quote span indices by the number of quotes that have been inserted
                    quote_spans = fix_quote_spans(quote_spans, quote_indices)
                    dep = fix_dependencies(dep, quote_indices)
                    
                print >> parg_out, dep
                print >> ccg_out , ccg_bundle
    
ptb_file_re = re.compile(r'(\d{2})/wsj_\d{2}(\d{2})\.mrg$')
def main(argv):
    parser = OptionParser()

    register_builtin_switches(parser)                        
    opts, args = parser.parse_args(argv)
    
    check_for_required_args(opts)
    
    quoter_class = {
        'span': SpanQuoter,
#        'lca' : LCAQuoter
    }[opts.quote_method]
    punct_class = {
        'swap' : SwapComma,
        'shift': ShiftComma
    }.get(opts.punct_method, None)
    quoter = quoter_class(punct_class)
    
    remaining_args = args[1:]
    if not remaining_args:
        # If no sec/doc specifiers are given, assume 'all sections all documents'
        remaining_args.append(':')
        
    ptb_files_spec = parse_requested_derivs(remaining_args)
    
    for sec_glob, doc_glob in ptb_files_spec:
        for ptb_file in glob(os.path.join(opts.penn_in, sec_glob, "wsj_%s%s.mrg" % (sec_glob, doc_glob))):
            info("Processing %s", ptb_file)
            
            matches = ptb_file_re.search(ptb_file)
            if matches and len(matches.groups()) == 2:
                sec, doc = matches.groups()
                
                ccg_file =  os.path.join(opts.ccg_in, 'AUTO', sec, "wsj_%s%s.auto" % (sec, doc))
                deps_file = os.path.join(opts.ccg_in, 'PARG', sec, "wsj_%s%s.parg" % (sec, doc))
                
                if not opts.quiet:
                    if not os.path.exists(ccg_file):
                        warn("No corresponding CCGbank file %s for Penn file %s", ccg_file, ptb_file)
                    if not os.path.exists(deps_file):
                        warn("No corresponding CCGbank dependency file %s for CCG file %s", deps_file, ccg_file)
                        
                ccg_auto_dir, ccg_parg_dir = [os.path.join(opts.outdir, part, sec) for part in ('AUTO', 'PARG')]
                if not os.path.exists(ccg_auto_dir): os.makedirs(ccg_auto_dir)
                if not os.path.exists(ccg_parg_dir): os.makedirs(ccg_parg_dir)
                
                ccg_auto_out, ccg_parg_out = (os.path.join(ccg_auto_dir, 'wsj_%s%s.auto' % (sec, doc)),
                                              os.path.join(ccg_parg_dir, 'wsj_%s%s.parg' % (sec, doc)))
                                              
                process(ptb_file, ccg_file, deps_file, ccg_auto_out, ccg_parg_out, 
                                     opts.higher, opts.quotes, quoter)
                
            else:
                warn("Could not find, so ignoring %s", ptb_file)

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError: pass
    
    main(sys.argv)