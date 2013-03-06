from munge.proc.filter import Filter
from apps.util.tgrep_tabulation import TgrepTabulation

ProdropRuleCount = TgrepTabulation({
    'tv_subj_prodrop': '"S[dcl]/NP" <1 "(S[dcl]\NP)/NP" #<1',
    'tv_obj_prodrop':  '"S[dcl]\NP" <1 "(S[dcl]\NP)/NP" #<1',
    'iv_subj_prodrop': '"S[dcl]" <1 "S[dcl]\NP" #<1',
    'dtv_subj_prodrop': '"(S[dcl]/NP)/NP" <1 "((S[dcl]\NP)/NP)/NP" #<1',
    'dtv_obj_prodrop': '"(S[dcl]\NP)/NP" <1 "((S[dcl]\NP)/NP)/NP" #<1',
})
    