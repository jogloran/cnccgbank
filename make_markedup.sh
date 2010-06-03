#! /bin/bash

if [[ $# -lt 2 ]]; then
    echo "Usage:"
    echo "    $0 threshold corpus"
    exit 1
fi

threshold=$1; shift
corpus=$@

# count all categories over the corpus
egrep -ho '<L [^ ]+' $corpus | cut -c3- | sort | uniq -c | sort -rn | \
    # filter out categories under the threshold
    gawk "(\$1 >= $threshold) { print \$2 }" | \
    # generate markedup
    python -m'apps.cn.mkmarked' | \
    # insert [X] feature variables
    perl -ne 's/S(?!\[)/S\[X\]/g if $_ =~ /^\s+/; print' | \
    # add dependency slots and 'ignore' entries
    perl -ne '$i=1; s/(?=\){_})/$v="<$i>";++$i;$v;/ge; s/^\t\d+/"\t".($i-1)/ge; print $_; if ($i>0) {print "\t$_ ignore\n" for 1..($i-1)}'
