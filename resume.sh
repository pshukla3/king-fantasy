#!/bin/bash
set -e
set -o pipefail
cd ~/nfl-engine
source venv/bin/activate
python3 378_points.py | tail -1
python3 379_boardui.py | tail -1
python3 405_ptstab.py | tail -2
python3 389_liveinj.py | tail -2
python3 351_slmap.py | tail -4
python3 409_leaguesim.py | tail -4
python3 412_connect.py | tail -2
python3 415_idmap.py | tail -3
python3 353_hub.py | tail -1
python3 416_hubtabs.py | tail -4
python3 417_musched.py | tail -2
python3 418_matchup.py | tail -3
python3 419_pnews.py | tail -2
python3 420_hist.py | tail -2
python3 421_card.py | tail -1
python3 422_myteam.py | tail -2
python3 424_waiv.py | tail -4
python3 425_waivui.py | tail -2
python3 426_games.py | tail -2
python3 427_standings.py | tail -2
python3 428_power.py | tail -3
python3 435_startsit.py | tail -2
python3 436_startsit.py | tail -2
python3 431_score.py | tail -1
python3 432_wksnap.py | tail -2
python3 433_wkpts.py | tail -3
python3 429_scores.py | tail -3
python3 423_chargers.py | tail -8
python3 320_brand.py | tail -1
python3 338_lpts.py | tail -2
python3 339_leaders_ui.py | tail -3
python3 386_dark.py | tail -10
python3 328_live.py | tail -1

echo "--- ship ---"
python3 434_scorebar.py | tail -3
python3 414_dedupe.py | tail -3
# re-assert card wiring (a later script re-adds _card.js)
python3 495_wirecard.py || exit 1
python3 496_iframeshim.py || exit 1
python3 522_homewk.py || exit 1
python3 529_homeorder.py || exit 1
python3 511_bust.py || exit 1
python3 510_guard_snap.py || exit 1
python3 413_verify.py || exit 1
cp vaporai.html site/index.html
python3 177_gate.py
netlify deploy --dir=site --prod
