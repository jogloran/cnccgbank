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
        