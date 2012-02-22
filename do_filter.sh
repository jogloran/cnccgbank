#! /bin/bash

filtered_output_file=$1

rm -rf filtered
./t -q -lapps.cn.badatom --bad-atom filtered final/*/*
cat filtered/* > "$filtered_output_file"
