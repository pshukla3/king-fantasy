#!/bin/bash
# full rebuild, raw data -> live site. ~15 min.
set -e
set -o pipefail
cd ~/nfl-engine
source venv/bin/activate

echo "=== 1. DATA REFRESH ==="
python3 98_news.py          | tail -2
python3 79_injuries.py      | tail -2

echo "=== 2. BASE BOARD ==="
python3 92_board_fix.py     | tail -2
python3 93_finalize.py      | tail -2
python3 115_roster_fix.py   | tail -2
python3 128_team_fix.py     | tail -2
python3 119_movers.py       | tail -2

echo "=== 3. QB (147 model) ==="
python3 156_depth_fix.py    | tail -2
python3 147_qb_v4.py        | tail -2
python3 165_qb_scale_final.py | tail -3

echo "=== 4. K / DST / UNIVERSE ==="
python3 126_kdst_fill.py    | tail -2
python3 202_defenses.py     | tail -3
python3 203_full_universe.py | tail -3

echo "=== 5. TRAIN (walk-forward validated) ==="
python3 211_mean_model.py   | tail -4
python3 212_residuals.py    | tail -3
python3 213_resid_shape.py  | tail -4

echo "=== 6. PROJECT ==="
python3 214_project_2026.py | tail -2
python3 218_rookies.py      | tail -2
python3 219_rookie_fix.py   | tail -4

echo "=== 7. REALITY CHECK (cuts, status) ==="
python3 215_roster_audit.py | tail -2
python3 216_purge.py        | tail -4
python3 217_injury_news.py  | tail -3

echo "=== 8. MERGE + RANK BY VORP ==="
python3 220_merge.py        | tail -4
python3 221_vorp_rank.py    | tail -4
cp board_final.csv board_pre_adp.csv
python3 232_apply_adp.py    | tail -3
python3 221_vorp_rank.py    | tail -8

python3 226_bye.py          | tail -2

echo "=== 9. SITE ==="
bash 223_ship.sh
