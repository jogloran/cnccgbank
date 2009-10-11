#! /bin/bash

paths=$@
rm -rf ./final;
./t -q -lapps.cn.output -r CCGbankStyleOutput final -0 -R AugmentedPTBReader $paths
