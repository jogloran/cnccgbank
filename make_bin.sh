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

echo "$TARGET"

# Tag derivations
echo Tagging derivations.
rm -rf ./tagged/"$TARGET";  ./t -q -lapps.cn.tag -r TagStructures tagged -0 corpora/cptb/bracketed/"$TARGET"
./t -q -w tagged_dots tagged/"$TARGET"

# Binarise derivations
echo Binarising derivations.
rm -rf ./binarised/"$TARGET";  ./t -q -lapps.cn.binarise -r Binariser binarised -0 tagged/"$TARGET"
# Make graphs
./t -q -w binarised_dots binarised/"$TARGET"
