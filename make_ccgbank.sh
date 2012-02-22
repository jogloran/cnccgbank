#! /bin/bash

# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

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
