#!/bin/bash
set -e
set -o pipefail
cd ~/nfl-engine
source venv/bin/activate

echo "--- data ---"
python3 98_news.py        | tail -2
python3 79_injuries.py    | tail -2
python3 92_board_fix.py   | tail -2
python3 93_finalize.py    | tail -2
python3 115_roster_fix.py | tail -2

echo "--- board repairs (93 wipes all of these) ---"
python3 119_movers.py     | tail -5
python3 120_wr_board.py   | tail -2
python3 126_kdst_fill.py  | tail -4
python3 125_calibrate.py  | tail -6

echo "--- ui (order: 112, 113, 114) ---"
python3 112_ui_v4.py      | tail -2
python3 113_home.py       | tail -8
python3 114_theme.py      | tail -7

echo "--- ship ---"
cp vaporai.html site/index.html
netlify deploy --dir=site --prod
