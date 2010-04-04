#! /bin/bash

break_flag=
dir_suffix=
while getopts 's:f' OPTION
do
    case $OPTION in
        s) dir_suffix="_$OPTARG"
        ;;
        f) break_flag=-b
        ;;
    esac
done
shift $(($OPTIND - 1))

if [[ $1 == "all" || $1 == "*" ]]; then
    SECTION=""
    TARGET="*"
elif [[ $1 =~ ^[0-9]{2}$ ]]; then
    SECTION=${1:-00}
    TARGET="chtb_${SECTION}*"
else
    TARGET=`basename $1`
fi

function do_fix {
    fix_suffix=$1; shift
    filter_name=$1; shift
    paths=$@

    echo "[`date +%c`] Applying fix $filter_name... -> $paths"

    rm -rf ./fixed_${fix_suffix}$dir_suffix/${TARGET}
    ./t -q -lapps.cn.fix_${fix_suffix} -r $filter_name fixed_${fix_suffix}$dir_suffix -0 "$paths" 2>&1 | tee ${fix_suffix}_errors 
    #rm -rf ./fixed_${fix_suffix}; ./t -lapps.cn.fix_${fix_suffix} -r $filter_name fixed_${fix_suffix} -0 "$paths"
    echo "Making DOTs for $filter_name..."
    #./t -q -D fixed_${fix_suffix}_dots -R AugmentedPTBReader fixed_${fix_suffix}/*
}

do_fix rc FixExtraction labelled$dir_suffix/"$TARGET"
do_fix adverbs FixAdverbs fixed_rc$dir_suffix/"$TARGET"
do_fix np FixNP fixed_adverbs$dir_suffix/"$TARGET"
