#!/bin/bash

cd ../python/
python3 normalize.py --type ttree
python3 normalize.py --type rntuple

cd ../data/
ls -lh ttree/normalize.root
ls -lh rntuple/normalize.root

cd ../bash/
