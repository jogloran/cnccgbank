from distutils.core import setup, Extension

setup(name='pressplit', ext_modules=[ Extension('pressplit', sources=['pressplit.c']) ])

