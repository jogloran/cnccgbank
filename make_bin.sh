#! /bin/bash

if [[ $1 == "all" ]]; then
    SECTION=""
else
    SECTION=${1:-00}
fi

# Tag derivations
rm -rf ./tagged/chtb_${SECTION}*; ./t -q -lmunge.proc.cn.count -r TagStructures tagged -0 corpora/cptb/bracketed/chtb_${SECTION}*
./t -q -w tagged_dots tagged/chtb_${SECTION}*

# Binarise derivations
rm -rf ./binarised/chtb_${SECTION}*; ./t -q -lapps.cn.binarise -r Binariser binarised -0 tagged/chtb_${SECTION}*
# Make graphs
./t -q -w binarised_dots binarised/chtb_${SECTION}*
