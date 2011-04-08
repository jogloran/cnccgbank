#! /bin/bash

dir_suffix_arg=
while getopts 'c:s:h' OPTION
do
    case $OPTION in
        c) corpus_dir_arg="-c $OPTARG" ;;
        s) dir_suffix_arg="-s $OPTARG" ;;
        h) echo "$0 [-c corpus_dir] [-s work_dir_suffix] [SEC|all]"
           exit 1 ;;
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

echo Started at: `date`
# Pass -s through to sub-scripts
./make_lab.sh $corpus_dir_arg $dir_suffix_arg "$TARGET" \
&& ./make_fix.sh $dir_suffix_arg "$TARGET" \
&& ./make_ccgbank.sh $dir_suffix_arg "$TARGET"  \
#&& ./t -q -D final_dots final/"$TARGET" 
echo Finished at: `date`
