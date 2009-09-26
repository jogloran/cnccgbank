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

./make_lab.sh "$TARGET"
./make_fix.sh "$TARGET"
./make_ccgbank.sh fixed_np/"$TARGET"
