#! /bin/bash

if [[ $1 == "all" ]]; then
    SECTION=""
else
    SECTION=${1:-00}
fi

./make_bin.sh $SECTION

rm -rf ./labelled/chtb_${SECTION}*; ./t -q -lapps.cn.catlab -r LabelNodes labelled -0 -R AugmentedPTBReader binarised/chtb_${SECTION}*

./t -q -w labelled_dots -R AugmentedPTBReader labelled/chtb_${SECTION}*
