#!/bin/bash
set -e
set -o pipefail
cd ~/nfl-engine
source venv/bin/activate

echo "=== presentation rebuild (board is NOT touched) ==="
python3 166_id_fix.py       | tail -2
python3 200_live_teams.py   | tail -2
python3 192_rank_page.py    | tail -2
python3 168_card_data.py    | tail -3
python3 169_card_page.py    | tail -2
python3 148_league_data.py  | tail -2
python3 152_rosters.py      | tail -2
python3 246_league_connect.py  | tail -2
python3 158_trade_page.py   | tail -2

echo "--- ui ---"
python3 112_ui_v4.py        | tail -1
python3 113_home.py         | tail -1
python3 114_theme.py        | tail -1

echo "--- ship ---"
cp vaporai.html site/index.html
python3 177_gate.py
netlify deploy --dir=site --prod | tail -4
