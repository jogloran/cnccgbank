# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import sys
from munge.util.config import config

muzzled = False
def muzzle(quiet=True):
    '''Sets the muzzled state to the value of _quiet_.'''
    global muzzled
    muzzled = quiet

def stream_report(stream, preface, msg, *fmts):
    '''Writes _msg_ to the given _stream_ preceded by _preface_, with
format arguments _fmts_.'''
    print >> stream, "%s: %s" % (preface, (msg % fmts))
    
def err(msg, *fmts):
    '''Issues an error _msg_ to stderr. Is not affected by the muzzled state.'''
    stream_report(sys.stderr, "error", msg, *fmts)
    
def warn(msg, *fmts):
    '''Issues a warning _msg_ to stderr except in the muzzled state.'''
    global muzzled
    if not muzzled:
        stream_report(sys.stderr, "warning", msg, *fmts)
    
def info(msg, *fmts):
    '''Issues an informational _msg_ to stderr except in the muzzled state.'''
    global muzzled
    if not muzzled:
        stream_report(sys.stderr, "info", msg, *fmts)
        
def msg(msg, *fmts):
    '''Issues a _msg_ to stderr regardless of the muzzled state.'''
    stream_report(sys.stderr, "msg", msg, *fmts)
    
def _make_debug(preface_maker):
    def debug(msg, *fmts):
        '''Issues a debug _msg_, prefaced by the name of the calling function.'''
        
        try:    caller_name = sys._getframe(1).f_code.co_name
        except: caller_name = "?"

        stream_report(sys.stderr, preface_maker(caller_name), msg, *fmts)
    return debug

if config.debug:
    if config.low_key_debug:
        debug = _make_debug(lambda caller: caller[0])
    else:
        debug = _make_debug(lambda caller: '[%s]' % caller)
else:
    from munge.util.func_utils import noop
    debug = noop
