from __future__ import with_statement

import re

from munge.proc.trace import Filter
from munge.proc.bases import AnnotatorFormReporter, AcceptRejectWithThreshold
from munge.util.err_utils import debug

from collections import defaultdict

class NullModeAnnotator(AnnotatorFormReporter, AcceptRejectWithThreshold):
    def __init__(self, threshold):
        AcceptRejectWithThreshold.__init__(self, threshold, (None, ))
        
    opt = "Z"
    long_opt = "make-null-mode-cands"
    
    arg_names = "THR"
    
class ApplicationModeAnnotator(AnnotatorFormReporter, AcceptRejectWithThreshold):
    def __init__(self, threshold):
        AcceptRejectWithThreshold.__init__(self, threshold, ("fwd_appl", "bwd_appl"))

    opt = "A"
    long_opt = "make-appl-mode-cands"

    arg_names = "THR"

class MakeAnnotator(Filter):
    '''Creates an annotator file from three sources: application and null-mode candidate slashes (automatic),
and composition mode candidates (determined manually).'''
    
    def __init__(self, threshold, manual_fn):
        Filter.__init__(self)
        
        self.appl_only_filter = ApplicationModeAnnotator(threshold)
        self.null_only_filter = NullModeAnnotator(threshold)

        self.manual_fn = manual_fn
        
    def parse_annoform(self, manual_fn):
        result = defaultdict(dict)
        
        with file(manual_fn, 'r') as f:
            for line in f:
                line = line.rstrip()
                category, replacement_mode_name, slash_index = line.split()
                slash_index = int(slash_index)
                # TODO: check no of fields
                
                result[category][slash_index] = replacement_mode_name
                
        return result
        
    def accept_comb_and_slash_index(self, leaf, comb, slash_index):
        for filter in (self.appl_only_filter, self.null_only_filter):
            filter.accept_comb_and_slash_index(leaf, comb, slash_index)
            
    def output(self):
        appl_accepted, _ = self.appl_only_filter.compute_accepts_and_rejects()
        null_accepted, _ = self.null_only_filter.compute_accepts_and_rejects()
        
        # Start by collecting the manually annotated slashes from the file
        aggregate = self.parse_annoform(self.manual_fn)

        for (set, mode_name) in ( (appl_accepted, 'apply'), (null_accepted, 'null') ):
            for (cat_string, slash_index, applied_frequency, total_frequency) in \
                sorted(set, key=lambda this: this[2], reverse=True):
                
#                 aggregate[re.sub(r'[-*@.]', '', cat_string)][slash_index] = mode_name
                # If there is a slash-mode entry in _aggregate_ already (from the manual list),
                # do not overwrite it.
                slash_to_mode_map = aggregate[re.sub(r'[-*@.]', '', cat_string)]
                if slash_index not in slash_to_mode_map:
                    debug("Slash %d of %s will have mode %s", slash_index, cat_string, mode_name)
                    slash_to_mode_map[slash_index] = mode_name
                else:
                    debug("Not overwriting slash %d of %s", slash_index, cat_string)
                
        for (category_string, slashes) in aggregate.iteritems():
            for (slash_index, mode_name) in slashes.iteritems():
                print " ".join((category_string, mode_name, str(slash_index)))
                
                
    opt = "V"
    long_opt = "make-annotator"
    
    arg_names = "THR,MANUAL"