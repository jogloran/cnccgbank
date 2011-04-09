#! /bin/bash

basedir=$1
shift

for f in $@; do
    fn=`basename "$f"`
    sec=${fn/chtb_/}; sec=${sec/.fid/}; sec=${sec%??}

    if [ ! -d "$basedir/$sec" ]; then
        mkdir -p "$basedir/$sec"
    fi
    cp -r "$f" "$basedir/$sec"
done
