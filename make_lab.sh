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


./make_bin.sh $1

rm -rf ./labelled/"$TARGET"; ./t -lapps.cn.catlab -r LabelNodes labelled -0 -R AugmentedPTBReader binarised/"$TARGET"

./t -w labelled_dots -R AugmentedPTBReader labelled/"$TARGET"
