#! /bin/bash

if [[ $1 == "all" || $1 == "*" ]]; then
    SECTION=""
    TARGET="*"
elif [[ $1 =~ ^[0-9]{2}$ ]]; then
    SECTION=${1:-00}
    TARGET="chtb_${SECTION}*"
else
    TARGET=`basename $1`
fi

echo "make_bin operating on $TARGET"

# Tag derivations
echo Tagging derivations.
echo rm -rf ./tagged/"$TARGET";
echo ./t -q -lapps.cn.tag -r TagStructures tagged -0 corpora/cptb/bracketed/"$TARGET"
echo ./t -q -w tagged_dots tagged/"$TARGET"

# Binarise derivations
echo Binarising derivations.
echo rm -rf ./binarised/"$TARGET";
echo ./t -q -lapps.cn.binarise -r Binariser binarised -0 tagged/"$TARGET"
# Make graphs
echo ./t -q -w binarised_dots binarised/"$TARGET"
