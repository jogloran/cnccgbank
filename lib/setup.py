# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

from distutils.core import setup, Extension

setup(name='pressplit', ext_modules=[ Extension('pressplit', sources=['pressplit.c']) ])
setup(name='pressplit2', ext_modules=[ Extension('pressplit2', sources=['pressplit2.cc']) ])
#setup(name='exthash', ext_modules=[ Extension('exthash', sources=['hash.c']) ])

