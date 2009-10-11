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

echo Started at: `date`
./make_lab.sh $1
./make_fix.sh $1
./make_ccgbank.sh fixed_np/"$TARGET"
./t -w final_dots final/"$TARGET" 
echo Finished at: `date`
