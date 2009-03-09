#! /bin/bash

function do_fix {
    fix_suffix=$1; shift
    filter_name=$1; shift
    paths=$@

    rm -rf ./fixed_${fix_suffix}; ./t -lapps.cn.fix_${fix_suffix} -r $filter_name fixed_${fix_suffix} -0 -R AugmentedPTBReader $paths
    ./t -q -w fixed_${fix_suffix}_dots -R AugmentedPTBReader fixed_${fix_suffix}/*
}

paths=$@
do_fix rc FixExtraction $paths #2> rc_errors
#do_fix prodrop FixProDrop fixed_rc/*
#do_fix adverbs FixAdverbs fixed_prodrop/*
