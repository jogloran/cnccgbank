from apps.util.tgrep_tabulation import TgrepTabulation

RCConfigurations = TgrepTabulation({
    'rel_subjgap':
    '* < { /CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < { /CP/ < { /IP/ << { /NP-SBJ/ < { "-NONE-" & ^/\*T\*-\d+/ } $ /VP/=V } } < /DEC/ } }',
    'rel_objgap':
    '* < { /CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < { /CP/ < { /IP/ << { /NP-OBJ/ < { "-NONE-" & ^/\*T\*-\d+/ } $ /V[VECA]|VRD|VSB|VCD/=V } } < /DEC/ } }',
    'rel_nogap':
    '* < { /CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < { /CP/ < { /IP/ << { /NP-SBJ/ ! < { "-NONE-" & ^/\*T\*-\d+/ } $ /VP/=V } } < /DEC/ } }',
    'nullrel_gap':
    '* < { /CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < {          /IP/ << { /NP-SBJ/ < { "-NONE-" & ^/\*T\*-\d+/ } $ /VP/=V } } }',
    'nullrel_nogap':
    '* < { /CP/ <1 { /WHNP/ < { "-NONE-" & ^/\*OP\*/=T } } < {          /IP/ << { /NP-SBJ/ ! < { "-NONE-" & ^/\*T\*-\d+/ } $ /VP/=V } } }',
})
