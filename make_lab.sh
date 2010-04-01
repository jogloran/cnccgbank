#! /bin/bash

if [ -f '.trace_break' ]; then
    break_flag=-b
else
    break_flag=
fi

if [[ $1 == "all" || $1 == "*" ]]; then
    SECTION=""
    TARGET="*"
elif [[ $1 =~ ^[0-9]{2}$ ]]; then
    SECTION=${1:-00}
    TARGET="chtb_${SECTION}*"
else
    TARGET=`basename $1`
fi

./make_bin.sh "$TARGET" && \

echo Doing category labelling.
rm -rf ./labelled/"$TARGET";
./t -q $break_flag -lapps.cn.catlab -r LabelNodes labelled -0 binarised/"$TARGET" 2>&1 | tee lab_errors 

echo Making DOTs.
#./t -q -D labelled_dots -R AugmentedPTBReader labelled/"$TARGET"
