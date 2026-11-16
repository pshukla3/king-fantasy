#!/bin/bash
set -e
cd ~/nfl-engine
source venv/bin/activate
W=${1:?usage: bash newrank.sh 12}
echo "Copy your ranking list now, then press Return"
read
pbpaste > ranks/raw$W.txt
wc -l ranks/raw$W.txt
python3 532_rankparse2.py $W
python3 525_rankin.py $W
