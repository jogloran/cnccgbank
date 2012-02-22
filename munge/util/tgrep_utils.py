# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from munge.proc.tgrep.tgrep import find_first

def get_first(*args, **kwargs):
    '''Returns one tgrep result, or None if no nodes match.'''
    try:
        return find_first(*args, **kwargs).next()
    except StopIteration:
        return None