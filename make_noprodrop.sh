# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

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
