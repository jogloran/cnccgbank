from __future__ import with_statement
from munge.proc.filter import Filter
import os, re

class OutputDerivation(object):
    '''Writes out a derivation to disk.'''
    def __init__(self, transformer=None, fn_template=None):
        '''Where _transformer_ is a function which receives each derivation bundle and
returns the string to write, and _fn_template_ is a format string with two format
arguments (the section and document #), creates an OutputDerivation.'''
        self.transformer = transformer or (lambda x: x.derivation)
        self.fn_template = fn_template or "chtb_%02d%02d.fid"
        
    def write_derivation(self, bundle):
        if not os.path.exists(self.outdir): os.makedirs(self.outdir)
        output_filename = os.path.join(self.outdir, self.fn_template % (bundle.sec_no, bundle.doc_no))

        with file(output_filename, 'a') as f:
            print >>f, self.transformer(bundle)

class OutputPrefacedPTBDerivation(OutputDerivation):
    '''Writes out PTB nodes one to a line, each preceded by a preface line with that
node's document ID.'''
    def __init__(self):
        def fix_label(label):
            matches = re.match(r'(\d+):(\d+)\((\d+)\)', label)
            
            if matches and len(matches.groups()) == 3:
                sec, doc, deriv = map(int, matches.groups())
                return "wsj_%02d%02d.%d" % (sec, doc, deriv)
            raise Exception, "Invalid label %s" % label

        def make_header(bundle):
            return 'ID=%s PARSER=GOLD NUMPARSE=1' % fix_label(bundle.label())
            
        def printer(bundle):
            return '\n'.join((
                make_header(bundle),
                repr(bundle.derivation)))

        OutputDerivation.__init__(self, printer)

class OutputCCGbankDerivation(OutputDerivation):
    '''Writes out CCGbank nodes in the CCGbank format.'''
    def __init__(self):
        def fix_label(label):
            matches = re.match(r'(\d+):(\d+)\((\d+)\)', label)
            
            if matches and len(matches.groups()) == 3:
                sec, doc, deriv = map(int, matches.groups())
                return "wsj_%02d%02d.%d" % (sec, doc, deriv)
            raise Exception, "Invalid label %s" % label
                
        def make_header(bundle):
            return 'ID=%s PARSER=GOLD NUMPARSE=1' % fix_label(bundle.label())
            
        def printer(bundle):
            return '\n'.join((
                make_header(bundle), 
                bundle.derivation.ccgbank_repr()))

        OutputDerivation.__init__(self, printer)
        
class CCGbankStyleOutput(Filter, OutputCCGbankDerivation):
    def __init__(self, outdir):
        OutputCCGbankDerivation.__init__(self)
        self.outdir = outdir
        
    def accept_derivation(self, bundle):
        self.write_derivation(bundle)
