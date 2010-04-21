import sys
from apps.util.config import config

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
    '''Issues a _msg_ to stderr except in the muzzled state.'''
    stream_report(sys.stderr, "msg", msg, *fmts)
    
if config.low_key_debug:
    def debug(msg, *fmts):
        '''Issues a debug _msg_, prefaced by the name of the calling function.'''
        # global muzzled
        # if muzzled: return
    
        try:    caller_name = sys._getframe(1).f_code.co_name
        except: caller_name = "?"
    
        stream_report(sys.stderr, caller_name[0], msg, *fmts)
else:
    def debug(msg, *fmts):
        '''Issues a debug _msg_, prefaced by the name of the calling function.'''
        # global muzzled
        # if muzzled: return
    
        try:    caller_name = sys._getframe(1).f_code.co_name
        except: caller_name = "?"
    
        stream_report(sys.stderr, "[" + caller_name + "]", msg, *fmts)