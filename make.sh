#! /bin/bash

function msg {
    echo "[`date +%c`] $1"
}

if [ -f unanalysed ]; then
    ts=$(date +%Y%m%d.%H%M)
    mv unanalysed unanalysed_$ts
    ln -sf unanalysed_$ts unanalysed_prev
fi

dir_suffix_arg=
while getopts 's:' OPTION
do
    case $OPTION in
        s) dir_suffix_arg="-s $OPTARG"
        ;;
    esac
done
shift $(($OPTIND - 1))

started=`date +%c`
./make_clean.sh
time ./make_all.sh $dir_suffix_arg all && ./do_filter.sh && (python -m'apps.cn.find_unanalysed' '../terry/CCG/output/cn/filtered_corpus.txt' > unanalysed)

# Filter out derivations with [conj] leaves
msg "Filtering out derivations with [conj] leaves..."
perl -0777 -p -i.orig -e 's/.*\n.*<L [^ ]+\[conj\].*\n//g' ../terry/CCG/output/cn/filtered_corpus.txt

rm -rf data/{AUTO,PARG,train.piped}

# Kill known bad sentences
msg "Filtering rare categories and rules..."
./filter.py ../terry/CCG/output/cn/filtered_corpus.txt > filtered

msg "Creating directory structure..."
# Regroup filtered_corpus into section directories
./regroup.py filtered data/AUTO

msg "Creating PARGs..."
# Create PARGs
./t -q -lapps.cn.mkdeps -9 data/PARG filtered

msg "Rebracketing (X|Y)[conj] -> X|Y[conj]..."
# Rebracket [conj] as expected by C&C: (X|Y)[conj] becomes X|Y[conj]
perl -pi -e 's/\(([^\s]+)\)\[conj\]/$1\[conj\]/g' data/AUTO/*/*
perl -pi -e 's/\(([^\s]+)\)\[conj\]/$1\[conj\]/g' data/PARG/*/*

msg "Creating supertagger data..."
# Create supertagger training data in piped format
rm -rf piped
./t -q -lapps.cn.cnc -r PipeFormat piped "%w|%P|%s" -0 data/AUTO/00/*
cat piped/* > data/dev.piped

rm -rf piped
./t -q -lapps.cn.cnc -r PipeFormat piped "%w|%P|%s" -0 data/AUTO/{0[1-9],1*,2[0-8]}/*
cat piped/* > data/train.piped

rm -rf piped
./t -q -lapps.cn.cnc -r PipeFormat piped "%w|%P|%s" -0 data/AUTO/3[01]/*
cat piped/* > data/test.piped
ended=`date +%c`

echo "Run started: $started"
echo "Run ended:   $ended"
