#!/bin/bash

cd ../python/
python3 skimming.py

cd ../src/
root -q skimmed_ttree_to_rntuple.C

cd ../data/
ls -lh ttree/skimmed.root
ls -lh rntuple/skimmed.root

cd ../bash/
