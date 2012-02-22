# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from __future__ import with_statement
from munge.proc.filter import Filter
import os

class CommasOnly(Filter):
    def __init__(self, outdir):
        Filter.__init__(self)
        
        self.outdir = outdir
        
#    puncts = ", : ; ? !".split()
    puncts = (",",)
    def accept_derivation(self, bundle):
        if any(tok in self.puncts for tok in bundle.derivation.text()):
            self.write_derivation(bundle)
        
    def write_derivation(self, bundle):
        outpath = os.path.join(self.outdir, "%02d" % bundle.sec_no)
        if not os.path.exists(outpath): os.makedirs(outpath)
        
        output_filename = os.path.join(outpath, "wsj_%02d%02d.auto" % (bundle.sec_no, bundle.doc_no))

        with file(output_filename, 'a') as f:
            print >>f, bundle
        