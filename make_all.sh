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

echo Started at: `date`
./make_lab.sh "$TARGET" \
&& ./make_fix.sh "$TARGET" \
&& ./make_ccgbank.sh fixed_np/"$TARGET"  \
&& ./t -w final_dots final/"$TARGET" 
echo Finished at: `date`
