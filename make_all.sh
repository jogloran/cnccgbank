#! /bin/bash -eu

corpus_dir_arg=
dir_suffix_arg=
config_file_arg=
corpus_dir=corpora/cptb/bracketed
dir_suffix=
config_file=config.yml
undo_topicalisation=false
while getopts 'c:s:C:hT' OPTION
do
    case $OPTION in
        C) config_file_arg="-C $OPTARG" ; config_file="$OPTARG" ;;
        c) corpus_dir_arg="-c $OPTARG" ; corpus_dir="$OPTARG" ;;
        s) dir_suffix_arg="-s $OPTARG" ; dir_suffix="$OPTARG" ;;
        T) undo_topicalisation=true ;;
        h) echo "$0 [-c corpus_dir] [-s work_dir_suffix] [-C config_file] [SEC|all]"
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

msg() {
    msg=$1
    echo "[`date +%c`] $msg"
}

apply() {
    srcdir=$1  # the data that goes in
    outdir=$2  # the data that comes out
    lib=$3     # the library
    filter=$4  # the filter
    errfile=$5 # write stderr from the run to this file
    comment=$6 # message to be displayed

    msg "$comment -> $outdir"
    rm -rf $outdir/"$TARGET"
    ./t -c $config_file -q -l$lib -r $filter $outdir -0 $srcdir/"$TARGET" 2>&1 | tee $errfile

    return ${PIPESTATUS[0]} # return the exit code of the first command in the pipe
}

echo Started at: `date`

# 0. Filter
apply "$corpus_dir" "filtered$dir_suffix" \
    apps.cn.clean Clean clean_errors \
    "Filtering derivations..."

if $undo_topicalisation; then
    apply "filtered$dir_suffix" "undone$dir_suffix" \
        apps.dis.undotop UndoTop undo_errors \
        "Undoing gapped topicalisation..."
    # 1. Tag
    apply "undone$dir_suffix" "tagged$dir_suffix" \
        apps.cn.tag TagStructures tag_errors \
        "Tagging derivations..."
else
    # 1. Tag
    apply "filtered$dir_suffix" "tagged$dir_suffix" \
        apps.cn.tag TagStructures tag_errors \
        "Tagging derivations..."
fi


# 2. Binarise
apply "tagged$dir_suffix" "binarised$dir_suffix" \
    apps.cn.binarise Binariser bin_errors \
    "Binarising derivations..."

# 3. Label
apply "binarised$dir_suffix" "labelled$dir_suffix" \
    apps.cn.catlab LabelNodes lab_errors \
    "Doing category labelling..."

# 4. Fix
apply "labelled$dir_suffix" "fixed_rc$dir_suffix" \
    apps.cn.fix_rc FixExtraction extr_errors \
    "Applying extraction fixes..."
apply "fixed_rc$dir_suffix" "fixed_adverbs$dir_suffix" \
    apps.cn.fix_adverbs FixAdverbs adverbs_errors \
    "Applying adverb fixes..."
apply "fixed_adverbs$dir_suffix" "fixed_np$dir_suffix" \
    apps.cn.fix_np FixNP np_errors \
    "Applying NP fixes..."

# 5. Output
msg "Outputting CCGbank format... -> final$dir_suffix"
rm -rf ./final$dir_suffix/${TARGET}
./t -q -lapps.cn.output -r CCGbankStyleOutput final$dir_suffix -0 \
    -c $config_file \
    -lapps.sanity -r SanityChecks -0 fixed_np$dir_suffix/${TARGET}

echo Finished at: `date`
