import sys

def warn(msg, *fmts):
    print >> sys.stderr, "Warning: %s" % (msg % fmts)