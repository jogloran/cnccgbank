usage() {
    echo "$0 [ctb base dir] [output dir]"
}

if [[ $# != 2 ]]; then
    usage
    exit 1
fi

basedir=$1
outdir=$2 

mkdir -p $outdir

for f in $basedir/*.fid; do
    fn=$(basename $f)
    sed 's/(-NONE- \*pro\*)/(PN 他)/' $basedir/$fn > $outdir/$fn 
done
