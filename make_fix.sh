#! /bin/bash

if [[ $1 == "all" ]]; then
    SECTION=""
    TARGET="*"
elif [[ $1 =~ ^[0-9]{2}$ ]]; then
    SECTION=${1:-00}
    TARGET="chtb_${SECTION}*"
#elif [ -f $1 ]; then
else
    TARGET=`basename $1`
#else
#    echo Invalid argument.
#    exit 1
fi

function do_fix {
    fix_suffix=$1; shift
    filter_name=$1; shift
    paths=$@

    echo "Applying fix $filter_name..."

    rm -rf ./fixed_${fix_suffix}; ./t -lapps.cn.fix_${fix_suffix} -r $filter_name fixed_${fix_suffix} -0 -R AugmentedPTBReader $paths
    #rm -rf ./fixed_${fix_suffix}; ./t -lapps.cn.fix_${fix_suffix} -r $filter_name fixed_${fix_suffix} -0 $paths
    echo "Making DOTs for $filter_name..."
    ./t -q -w fixed_${fix_suffix}_dots -R AugmentedPTBReader fixed_${fix_suffix}/*
}

paths=labelled/"$TARGET"
do_fix rc FixExtraction $paths #2> rc_errors
do_fix adverbs FixAdverbs fixed_rc/*
do_fix np FixNP fixed_adverbs/*
