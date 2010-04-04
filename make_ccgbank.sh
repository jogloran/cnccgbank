#! /bin/bash

dir_suffix=
while getopts 's:' OPTION
do
    case $OPTION in
        s) dir_suffix="_$OPTARG"
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

rm -rf ./final/${TARGET};
echo "[`date +%c`] Outputting CCGbank format... -> final$dir_suffix"
./t -q -lapps.cn.output -r CCGbankStyleOutput final$dir_suffix -0 -lapps.sanity -r SanityChecks -0 fixed_np$dir_suffix/${TARGET}
