import sys
import re
import os

from optparse import OptionParser
from glob import glob

from munge.util.err_utils import warn

DefaultLogFile = "quote_error#prints"

def register_builtin_switches(parser):
    parser.set_defaults(punct_method="shift",
                        quote_method="span",
                        quotes="both",
                        highest="left",
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
    
def fix_secdoc_string(secdoc):
    if secdoc is None:
        return '*'
    if len(secdoc) == 1:
        return '0' + secdoc
    return secdoc
    
deriv_re = re.compile(r'([*\d]+)?:([*\d]+)?')
def parse_requested_derivs(args):
    result = []
    
    for arg in args:
        match = deriv_re.match(arg)
        if match and len(match.groups()) == 2:
            sec, doc = map(fix_secdoc_string, match.groups())
            
            result.append( (sec, doc) )
            
    return result
    
ptb_file_re = re.compile(r'(\d{2})/wsj_\d{2}(\d{2})\.mrg$')
def main(argv):
    parser = OptionParser()

    register_builtin_switches(parser)                        
    opts, args = parser.parse_args(argv)
    
    remaining_args = args[1:]
    ptb_files_spec = parse_requested_derivs(remaining_args)
    
    for sec_glob, doc_glob in ptb_files_spec:
        for ptb_file in glob(os.path.join(opts.penn_in, sec_glob, "wsj_%s%s.mrg" % (sec_glob, doc_glob))):
            matches = ptb_file_re.search(ptb_file)
            if matches and len(matches.groups()) == 2:
                sec, doc = matches.groups()
                
                ccg_file =  os.path.join(opts.ccg_in, 'AUTO', sec, "wsj_%s%s.auto" % (sec, doc))
                deps_file = os.path.join(opts.ccg_in, 'PARG', sec, "wsj_%s%s.parg" % (sec, doc))
                
                if not opts.quiet:
                    if not os.path.exists(ccg_file):
                        warn("No corresponding CCGbank file %s for Penn file %s" % (ccg_file, ptb_file))
                    if not os.path.exists(deps_file):
                        warn("No corresponding CCGbank dependency file %s for CCG file %s" % (deps_file, ccg_file))
                        
                ccg_auto_dir, ccg_parg_dir = [os.path.join(opts.ccg_in, part, sec) for part in ('AUTO', 'PARG')]
                if not os.path.exists(ccg_auto_dir): os.makedirs(ccg_auto_dir)
                if not os.path.exists(ccg_parg_dir): os.makedirs(ccg_parg_dir)
                
                ccg_auto_out, ccg_parg_out = (os.path.join(ccg_auto_dir, 'wsj_%s%s.auto' % (sec, doc)),
                                              os.path.join(ccg_parg_dir, 'wsj_%s%s.auto' % (sec, doc)))
                                             
                print ccg_auto_out
                print ccg_parg_out
            else:
                warn("Could not find, so ignoring %s" % ptb_file)

if __name__ == '__main__':
    main(sys.argv)