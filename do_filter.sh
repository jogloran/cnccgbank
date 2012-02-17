#! /bin/bash

rm -rf filtered
./t -q -lapps.cn.badatom --bad-atom filtered final/*/*
cat filtered/* > filtered_corpus
