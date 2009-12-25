SECS=$@
TARGET=`echo $SECS | ruby -ne 'puts "{%s}" % ( $_.split.map {|e| "chtb_%02d*" % e} ).join(",")'`

eval ./t -q $break_flag -lapps.cn.tag -r TagStructures tagged -0 corpora/cptb/bracketed/$TARGET 2>&1 | tee tag_errors 
eval ./t -q $break_flag -lapps.cn.binarise -r Binariser binarised -0 tagged/$TARGET 2>&1 | tee bin_errors
eval ./t -q $break_flag -lapps.cn.catlab -r LabelNodes labelled -0 -R AugmentedPTBReader binarised/$TARGET 2>&1 | tee lab_errors 

function do_fix {
    fix_suffix=$1; shift
    filter_name=$1; shift
    paths=$@

    echo "Applying fix $filter_name..."
    echo to $paths

    rm -rf ./fixed_${fix_suffix}/${TARGET}
    eval ./t -q -lapps.cn.fix_${fix_suffix} -r $filter_name fixed_${fix_suffix} -0 -R AugmentedPTBReader $paths #2>&1 | tee ${fix_suffix}_errors 
    #rm -rf ./fixed_${fix_suffix}; eval ./t -lapps.cn.fix_${fix_suffix} -r $filter_name fixed_${fix_suffix} -0 "$paths"
    echo "Making DOTs for $filter_name..."
    #eval ./t -q -D fixed_${fix_suffix}_dots -R AugmentedPTBReader fixed_${fix_suffix}/*
}

do_fix rc FixExtraction labelled/$TARGET
do_fix adverbs FixAdverbs fixed_rc/$TARGET
do_fix np FixNP fixed_adverbs/$TARGET