#! /bin/bash

break_flag=
corpus_dir=corpora/cptb/bracketed
dir_suffix=
while getopts 'c:s:f' OPTION
do
    case $OPTION in
        c) corpus_dir="$OPTARG"
        ;;
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

# Tag derivations
echo "[`date +%c`] Tagging derivations... -> tagged$dir_suffix"
rm -rf ./tagged$dir_suffix/"$TARGET"
./t -q $break_flag -lapps.cn.tag -r TagStructures tagged$dir_suffix -0 "$corpus_dir/$TARGET" 2>&1 | tee tag_errors 
#./t -q -D tagged_dots tagged/"$TARGET"

# Binarise derivations
echo "[`date +%c`] Binarising derivations... -> binarised$dir_suffix"
rm -rf ./binarised$dir_suffix/"$TARGET"
./t  $break_flag -lapps.cn.binarise -r Binariser binarised$dir_suffix -0 tagged$dir_suffix/"$TARGET" 2>&1 | tee bin_errors
# Make graphs
#./t -q -D binarised_dots binarised/"$TARGET"
