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
        stream_report(sys.stderr, "info", msg, *fmts)
    
def debug(msg, *fmts):
    stream_report(sys.stderr, time.asctime(), msg, *fmts)
    