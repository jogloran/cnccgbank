import sys
import time

from munge.util.func_utils import noop_function

muzzled = False
def muzzle(quiet=True):
    global muzzled
    muzzled = quiet

def stream_report(stream, preface, msg, *fmts):
    print >> stream, "%s: %s" % (preface, (msg % fmts))
    
def err(msg, *fmts):
    stream_report(sys.stderr, "error", msg, *fmts)
    
def warn(msg, *fmts):
    global muzzled
    if not muzzled:
        stream_report(sys.stderr, "warning", msg, *fmts)
    
def info(msg, *fmts):
    global muzzled
    if not muzzled:
        stream_report(sys.stdout, "info", msg, *fmts)
        
def msg(msg, *fmts):
    stream_report(sys.stderr, "msg", msg, *fmts)
    
def debug(msg, *fmts):
    try:    caller_name = sys._getframe(1).f_code.co_name
    except: caller_name = "?"
    
    stream_report(sys.stderr, "[" + caller_name + "]", msg, *fmts)