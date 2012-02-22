# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import re

Prologue = r'\begin{tabular}{r|l}'
Epilogue = r'\end{tabular}'
RowTemplate = r'%s & %s \\'
def table_freqs(freqs):
    bits = [ Prologue ]
    for key, freq in sorted(freqs.iteritems(), reverse=True,
                            key=lambda e: e[1]):
        bits.append(RowTemplate % (freq, key))
    bits.append(Epilogue)
    
    return '\n'.join(bits)
    
def sanitise_category(cat):
    return re.sub(r'\\', r'\\bs ', cat)
        