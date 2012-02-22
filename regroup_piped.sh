#! /bin/bash

# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

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
