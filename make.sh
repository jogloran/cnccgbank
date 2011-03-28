#! /bin/bash

function msg {
    echo "[`date +%c`] $1"
}

if [ -f unanalysed ]; then
    ts=$(date +%Y%m%d.%H%M)
    mv unanalysed unanalysed_$ts
    ln -sf unanalysed_$ts unanalysed_prev
fi

corpus_dir_arg=
dir_suffix_arg=
final_dir=data
while getopts 'c:s:o:h' OPTION
do
    case $OPTION in
        c) corpus_dir_arg="-c $OPTARG" ;;
        s) dir_suffix_arg="-s $OPTARG" ;;
        o) final_dir="$OPTARG" ;;
        h) echo "$0 [-s dir-suffix] [-o output-dir] [-c corpus-dir]"
           exit 1
        ;;
    esac
done
shift $(($OPTIND - 1))

started=`date +%c`
./make_clean.sh
time ./make_all.sh $corpus_dir_arg $dir_suffix_arg all && ./do_filter.sh && (python -m'apps.cn.find_unanalysed' '../terry/CCG/output/cn/filtered_corpus.txt' > unanalysed)

# Filter out derivations with [conj] leaves
msg "Filtering out derivations with [conj] leaves..."
perl -0777 -p -i.orig -e 's/.*\n.*<L [^ ]+\[conj\].*\n//g' ../terry/CCG/output/cn/filtered_corpus.txt

rm -rf ${final_dir}/{AUTO,PARG,train.piped}

# Kill known bad sentences
msg "Filtering rare categories and rules..."
./filter.py ../terry/CCG/output/cn/filtered_corpus.txt > filtered

msg "Creating directory structure..."
# Regroup filtered_corpus into section directories
./regroup.py filtered ${final_dir}/AUTO

msg "Creating PARGs..."
# Create PARGs
./t -q -lapps.cn.mkdeps -9 ${final_dir}/PARG filtered

msg "Rebracketing (X|Y)[conj] -> X|Y[conj]..."
# Rebracket [conj] as expected by C&C: (X|Y)[conj] becomes X|Y[conj]
perl -pi -e 's/\(([^\s]+)\)\[conj\]/$1\[conj\]/g' ${final_dir}/AUTO/*/*
perl -pi -e 's/\(([^\s]+)\)\[conj\]/$1\[conj\]/g' ${final_dir}/PARG/*/*

msg "Creating supertagger data..."
# Create supertagger training data in piped format
rm -rf ${final_dir}/piped
./t -q -lapps.cn.cnc -r PipeFormat ${final_dir}/piped "%w|%P|%s" -0 ${final_dir}/AUTO/*/*
ended=`date +%c`

echo "Run started: $started"
echo "Run ended:   $ended"
