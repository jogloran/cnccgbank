#! /bin/bash

cur=`pwd`
pushd ../terry/CCG
./run_filter.sh output cn $cur/final/*/*
popd
