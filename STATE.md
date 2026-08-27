# nfl-engine state — 2026-08-27

## Live
https://accuracy.report  (Netlify project `shukieanalytics`)
Rebuild + ship:  ./deploy.sh

## Pipeline order (deploy.sh)
98_news -> 79_injuries -> 92_board_fix -> 93_finalize
-> 115_roster_fix -> 119_movers -> 120_wr_board
-> 126_kdst_fill -> 125_calibrate
-> 112_ui_v4 -> 113_home -> 114_theme -> netlify

93_finalize REBUILDS board_final.csv from scratch and wipes
119/120/126/125. Anything that edits the board must run after it.

## League (Sleeper, verified)
Double CheeseBurger, league_id 1312181058833240064, 10 teams
Slots: QB RB RB WR WR TE FLEX FLEX K DEF + 5 BN
Full PPR. rec +1, rec_yd .1, rec_td 6, rush_yd .1, rush_td 6,
fum_lost -2. ALL receiving bonuses zero.
pass_yd .04, pass_td 4, pass_int -2.

## Measured constants
Replacement ppg: QB 19.72 RB 11.73 WR 11.95 TE 9.75
K repl 8.08 (Butker exactly at replacement)
DST repl 6.86, persistence r=0.265
Reliability y/y: WR .765 TE .733 RB .709 QB .56 DST .265
Calibration (fit pre-2020, verified 2020+):
  QB 8.24 + .512x | RB 2.44 + .714x
  WR 2.46 + .746x | TE 2.04 + .701x
  out-of-sample MAE 2.779 -> 2.691 (+0.088)

## Rejected features (train/test, threshold +0.010)
117 WR volume x regressed efficiency  +0.003
121 WR TD regression                   +0.004
123 WOPR                               +0.002
Defense-vs-WR schedule persistence    -0.085 (noise)

## Known defects
- tgt_share in 118 uses season denominator, not week-level
- `interceptions` missing from weekly file -> passer rtg has 0 INTs
- Deebo Samuel: no roster match, hand-priced 10.0 ppg,
  fabricated player_id, blank depth_rank, live on the site
- Butker sorts last (no blend, sentinel-ranked)

## Next
127_trade.py — optimal-starting-lineup delta calculator,
prices off the calibrated board, wires into the My Team tab.
