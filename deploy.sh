#!/bin/bash
set -e
set -o pipefail
cd ~/nfl-engine
source venv/bin/activate

echo "--- data ---"
python3 280_news.py       | tail -4
python3 79_injuries.py    | tail -2
python3 92_board_fix.py   | tail -2
python3 93_finalize.py    | tail -2
python3 115_roster_fix.py | tail -2
python3 128_team_fix.py   | tail -3

echo "--- board repairs (93 wipes all of these) ---"
python3 119_movers.py     | tail -5
python3 120_wr_board.py   | tail -2
python3 126_kdst_fill.py  | tail -4
python3 125_calibrate.py  | tail -6
python3 250_adp_attach.py | tail -2
python3 323_dst_build.py | tail -2
python3 156_depth_fix.py   | tail -3
python3 147_qb_v4.py       | tail -3
python3 165_qb_scale_final.py | tail -8
python3 148_league_data.py | tail -3
python3 152_rosters.py     | tail -2
python3 246_league_connect.py | tail -2
python3 158_trade_page.py  | tail -2
python3 166_id_fix.py      | tail -4
python3 168_card_data.py   | tail -6
python3 169_card_page.py   | tail -4

echo "--- ui (order: 112, 113, 114) ---"
python3 112_ui_v4.py      | tail -2
python3 113_home.py       | tail -8
python3 114_theme.py      | tail -7
python3 284_gvfix.py
python3 288_shell.py
python3 442_railorder.py | tail -3
python3 289_nav2.py
python3 292_tf_v3.py | tail -3
python3 293_tf_page.py | tail -1
python3 295_accuracy.py | tail -1
python3 297_dist.py | tail -2
python3 296_rankings.py | tail -3
python3 298_tradecalc.py | tail -1
python3 302_tc_settings.py | tail -2
python3 326_dst_sync.py | tail -3
python3 345_injstat.py | head -2
python3 347_projadj.py | tail -3
python3 344_matchup.py | tail -3
python3 299_league_sim.py | tail -3
python3 300_search.py | tail -1
python3 311_qr.py | tail -2
python3 312_startsit.py | tail -1
python3 294_polish.py | tail -2
python3 306_theme.py | tail -2
python3 315_landing.py | tail -2
python3 317_auth.py | tail -1
python3 316_readable.py | tail -2
python3 319_hawks.py | tail -2
python3 354_guard.py
python3 367_injrisk.py | tail -2
python3 376_faces.py | tail -1
python3 397_apply.py | tail -3
python3 398_merge.py | tail -8
python3 402_dual_consensus.py | tail -6
python3 403_wk1adj.py | tail -3
python3 404_injweeks.py | tail -3
python3 368_board.py | tail -2
python3 453_defrank.py | tail -3
python3 460_qbinj.py | tail -6
python3 456_project.py | tail -3
python3 459_apply.py | tail -3
python3 446_wkadj.py | tail -6
# --- QB sim engine (20k sims/game) ---
# --- projection engines (20k sims/game) ---
# order matters: params -> shares -> sim -> merge -> vorp
python3 526_prod.py     || exit 1   # season actuals
python3 528_opp.py      || exit 1   # opportunity
python3 465_injtime.py   || exit 1   # injury timelines
python3 473_offense.py   || exit 1   # vegas implied totals
python3 470_qb.py        || exit 1   # qb params
python3 472_qbsim.py     || exit 1   # qb sim
python3 476_qbmerge.py   || exit 1
python3 488_qbindex.py   || exit 1   # qb quality index
python3 481_wr2.py       || exit 1   # wr/te params
python3 483_share.py     || exit 1   # target share norm
python3 482_wrsim.py     || exit 1   # wr/te sim
python3 490_rb.py        || exit 1   # rb params
python3 492_rbshare.py   || exit 1   # backfield share
python3 491_rbsim.py     || exit 1   # rb sim
python3 493_mergeall.py  || exit 1   # all -> board
python3 500_kickpull.py  || exit 1   # kicker roster
python3 501_kickopp.py   || exit 1   # FG opportunity
python3 502_kparams.py   || exit 1   # kicker params
python3 504_ksim.py      || exit 1   # kicker sim
python3 507_kfill.py     || exit 1   # fill missing rows
python3 508_adp.py       || exit 1   # one ADP scale
python3 506_kmerge.py    || exit 1   # kickers -> board
python3 477_vorp.py      || exit 1   # replacement level
python3 466_injapply.py  || exit 1   # injuries last
python3 512_freeagent.py || exit 1   # released players -> zero
python3 533_boardadd.py --write || exit 1
python3 534_unfreeze.py --write || exit 1
python3 527_rankapply.py --write || exit 1
python3 537_statline.py || exit 1
python3 509_kweek.py     || exit 1   # kickers -> weekly files
python3 516_lgstate.py   || exit 1   # live league state
python3 517_lgcalc.py    || exit 1   # luck + lineup proj
python3 518_lgsim.py     || exit 1   # season simulation
python3 519_lgextra.py   || exit 1   # power tab section
python3 489_cardata.py   || exit 1   # card data
python3 494_card2.py     || exit 1   # card renderer
python3 521_topwk.py || exit 1
python3 497_rankdata.py  || exit 1   # rankings from the live board
python3 495_wirecard.py  || exit 1
python3 496_iframeshim.py || exit 1   # wire clicks

python3 439_tcvalues.py | tail -6
python3 478_mock.py
python3 440_tradecalc.py | tail -2
python3 373_reasons.py | tail -1
python3 378_points.py | tail -1 || true
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
python3 538_layout.py || exit 1
python3 545_tiers.py || exit 1
python3 511_bust.py || exit 1
python3 535_resnap.py --write || exit 1
python3 510_guard_snap.py || exit 1
python3 413_verify.py || exit 1
cp vaporai.html site/index.html
python3 177_gate.py
netlify deploy --dir=site --prod
