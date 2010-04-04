#! /bin/bash

dir_suffix_arg=
while getopts 's:' OPTION
do
    case $OPTION in
        s) dir_suffix_arg="-s $OPTARG"
        ;;
    esac
done
shift $(($OPTIND - 1))
echo $dir_suffix_arg

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
./make_lab.sh $dir_suffix_arg "$TARGET" \
&& ./make_fix.sh $dir_suffix_arg "$TARGET" \
&& ./make_ccgbank.sh $dir_suffix_arg "$TARGET"  \
#&& ./t -q -D final_dots final/"$TARGET" 
echo Finished at: `date`
