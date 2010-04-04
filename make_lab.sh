#! /bin/bash

if [ -f '.trace_break' ]; then
    break_flag=-b
else
    break_flag=
fi

dir_suffix=
while getopts 's:' OPTION
do
    case $OPTION in
        s) dir_suffix_arg="$OPTARG"; dir_suffix="_$OPTARG"
        ;;
    esac
done
shift $(($OPTIND - 1))

if [[ $1 == "all" || $1 == "*" ]]; then
    SECTION=""
    TARGET="*"
elif [[ $1 =~ ^[0-9]{2}$ ]]; then
    SECTION=${1:-00}
    TARGET="chtb_${SECTION}*"
else
    TARGET=`basename $1`
fi

./make_bin.sh $dir_suffix_arg "$TARGET" && \

echo Doing category labelling.
rm -rf ./labelled$dir_suffix/"$TARGET";
./t -q $break_flag -lapps.cn.catlab -r LabelNodes labelled$dir_suffix -0 binarised$dir_suffix/"$TARGET" 2>&1 | tee lab_errors 

echo Making DOTs.
#./t -q -D labelled_dots -R AugmentedPTBReader labelled/"$TARGET"
