#! /bin/bash

corpus_dir_arg=
break_flag=
dir_suffix=
while getopts 'c:s:f' OPTION
do
    case $OPTION in
        c) corpus_dir_arg="-c $OPTARG" 
        ;;
        s) dir_suffix_arg="-s $OPTARG"; dir_suffix="_$OPTARG"
        ;;
        f) break_flag=-b
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

./make_bin.sh $corpus_dir_arg $dir_suffix_arg "$TARGET" && \

echo "[`date +%c`] Doing category labelling... -> labelled$dir_suffix"
rm -rf ./labelled$dir_suffix/"$TARGET"
./t -q $break_flag -lapps.cn.catlab -r LabelNodes labelled$dir_suffix -0 binarised$dir_suffix/"$TARGET" 2>&1 | tee lab_errors 

#echo Making DOTs.
#./t -q -D labelled_dots -R AugmentedPTBReader labelled/"$TARGET"
