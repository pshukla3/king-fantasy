#!/bin/bash
set -e
set -o pipefail
cd ~/nfl-engine
source venv/bin/activate

if [ -f league_rosters.csv ]; then
  cp league_rosters.csv league_rosters.prev.csv
fi

echo "=== LIVE ROSTER PULL FROM SLEEPER ==="
python3 166_id_fix.py      | tail -2
python3 148_league_data.py | tail -3
python3 152_rosters.py     | tail -3

echo ""
echo "=== MATCHUP ODDS + PROJECTED RECORD ==="
python3 235_odds.py | tail -20
