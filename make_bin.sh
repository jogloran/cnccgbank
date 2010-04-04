#! /bin/bash

if [ -f '.trace_break' ]; then
    break_flag=-b
else
    break_flag=
fi

dir_suffix=
while getopts 's:' OPTION
do
    case $OPTION in
        s) dir_suffix="_$OPTARG"
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

# Tag derivations
echo Tagging derivations.
rm -rf ./tagged/"$TARGET"
./t -q $break_flag -lapps.cn.tag -r TagStructures tagged$dir_suffix -0 corpora/cptb/bracketed/"$TARGET" 2>&1 | tee tag_errors 
#./t -q -D tagged_dots tagged/"$TARGET"

# Binarise derivations
echo Binarising derivations.
rm -rf ./binarised/"$TARGET"
./t -q $break_flag -lapps.cn.binarise -r Binariser binarised$dir_suffix -0 tagged$dir_suffix/"$TARGET" 2>&1 | tee bin_errors
# Make graphs
#./t -q -D binarised_dots binarised/"$TARGET"
