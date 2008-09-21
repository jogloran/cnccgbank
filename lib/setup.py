from distutils.core import setup, Extension

setup(name='pressplit', ext_modules=[ Extension('pressplit', sources=['pressplit.c']) ])
#setup(name='exthash', ext_modules=[ Extension('exthash', sources=['hash.c']) ])

