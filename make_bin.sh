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

# Tag derivations
echo Tagging derivations.
rm -rf ./tagged/"$TARGET"
./t -q -lapps.cn.tag -r TagStructures tagged -0 corpora/cptb/bracketed/"$TARGET" 2>&1 | tee tag_errors 
#./t -q -D tagged_dots tagged/"$TARGET"

# Binarise derivations
echo Binarising derivations.
rm -rf ./binarised/"$TARGET"
./t -q -lapps.cn.binarise -r Binariser binarised -0 tagged/"$TARGET" 2>&1 | tee bin_errors
# Make graphs
#./t -q -D binarised_dots binarised/"$TARGET"
