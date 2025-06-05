#!/bin/bash

cd ../python/
python3 features.py --type ttree
python3 features.py --type rntuple

cd ../data/
ls -lh ttree/features.root
ls -lh rntuple/features.root

cd ../bash/
