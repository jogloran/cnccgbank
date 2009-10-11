#! /bin/bash

paths=$@
echo rm -rf ./final;
echo ./t -q -lapps.cn.output -r CCGbankStyleOutput final -0 -R AugmentedPTBReader $paths
