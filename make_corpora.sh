#! /bin/bash

CORPORA=$1
CCGBANK=$2
WSJ=$3

echo "Making corpus directories..."
# Copy original PTB and CCGbank corpora to designated directory
if [ -d $CCGBANK/AUTO && -d $CCGBANK/PARG ]; then
    mkdir -p $CORPORA/ccgbank
    cp -LR $CCGBANK/{AUTO,PARG} $CORPORA/ccgbank
fi

if [ -d $WSJ ]; then
    mkdir -p $CORPORA/wsj
    cp -LR $WSJ $CORPORA/wsj
fi

echo "Applying malformed CCGbank category patches..."
# Apply CCGbank malformed category patches
patch $CORPORA/ccgbank/AUTO/05/wsj_0595.auto < patches/wsj_0595.auto.patch
patch $CORPORA/ccgbank/AUTO/21/wsj_2161.auto < patches/wsj_2161.auto.patch

echo "Applying tokenisation patches..."
# Apply the tokenisation patches
echo "\tApplying WSJ tokenisation patch..."
# Apply WSJ tokenisation patch
./s -i $CORPORA/wsj -o $CORPORA/wsj < scripts/manual_script

echo "\tApplying CCGbank tokenisation patch..."
# Apply CCGbank tokenisation patch
./s -i $CORPORA/ccgbank/AUTO -o $CORPORA/ccgbank/AUTO -f ccg < scripts/manual_ccg_script
echo "\tApplying CCGbank dependency patches..."
# Apply CCGbank dependency patches
patch $CORPORA/ccgbank/PARG/06/wsj_0687.parg < patches/wsj_0687.parg.patch
patch $CORPORA/ccgbank/PARG/21/wsj_2161.parg < patches/wsj_2161.parg.patch

echo "Fixing mis-quoted derivations in PTB..."
# Fix mis-quotes in PTB
python -m'apps.make_surgery' $CORPORA/wsj > fix_ptb_misquotes
./s -i $CORPORA/wsj -o $CORPORA/wsj < fix_ptb_misquotes
rm fix_ptb_misquotes

# We now have fixed versions of PTB and CCGbank

echo "Generating quoted CCGbank..."
# 1. Generate quoted version of CCGbank
./q -i $CORPORA/wsj -I $CORPORA/ccgbank -o $CORPORA/ccgbank_quoted

echo "Generating comma munged CCGbank..."
# 2. Generate comma munged version of CCGbank
# Generate comma munge files for CCGbank
python -m'apps.make_comma_surgery' $CORPORA/ccgbank/AUTO > ccgbank_communge
# Copy original CCGbank
cp -r $CORPORA/ccgbank $CORPORA/ccgbank_munged
# Overwrite in place with comma munge changes
./s -i $CORPORA/ccgbank_munged/AUTO -o $CORPORA/ccgbank_munged/AUTO < ccgbank_communge
rm ccgbank_communge

echo "Generating comma munged & quoted CCGbank..."
# 3. Generate comma munged, quoted version of CCGbank
# Generate comma munge files for CCGbank
python -m'apps.make_comma_surgery' $CORPORA/ccgbank_quoted/AUTO > ccgbank_quoted_communge
# Copy original CCGbank
cp -r $CORPORA/ccgbank_quoted $CORPORA/ccgbank_quoted_munged
# Overwrite in place with comma munge changes
./s -i $CORPORA/ccgbank_quoted_munged/AUTO -o $CORPORA/ccgbank_quoted_munged/AUTO < ccgbank_quoted_communge
rm ccgbank_quoted_communge

echo "Done."