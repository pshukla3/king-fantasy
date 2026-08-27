import pandas as pd, engine

LEAGUE = {
    "teams": 10,
    "rounds": 15,
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"],
    "scoring": {"pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "rush_yd": 0.1,
                "rush_td": 6, "rec": 1.0, "rec_yd": 0.1, "rec_td": 6, "fum_lost": -2},
}

proj = pd.read_csv("stat_projections_2026.csv", low_memory=False)
hist = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
birth = pd.read_csv("player_id_crosswalk.csv", low_memory=False)[["gsis_id", "birthdate"]]
birth = birth.dropna().drop_duplicates("gsis_id")

board, rel, repl = engine.build_board(proj, LEAGUE, hist, birth)
print("reliability:", {k: round(v, 3) for k, v in rel.items()})
print("replacement:", {k: round(v, 2) for k, v in repl.items()})
board.to_csv("final_board.csv", index=False)

cols = ["overall_rank", "player_display_name", "position", "pos_rank", "team", "age", "points", "vorp", "value"]
print("\n=== FINAL BOARD: TOP 60 ===")
print(board[cols].head(60).round(2).to_string(index=False))

T, R = LEAGUE["teams"], LEAGUE["rounds"]
picks = board.head(T * R).reset_index(drop=True)
print(f"\n=== SNAKE DRAFT — {T} teams x {R} rounds ===")
i = 0
for rd in range(1, R + 1):
    order = list(range(1, T + 1)) if rd % 2 else list(range(T, 0, -1))
    print(f"\n--- Round {rd} ---")
    for j, tm in enumerate(order, start=1):
        p = picks.iloc[i]
        print(f"  {rd}.{j:02d} (#{i+1:3d})  Team{tm:2d}  {p['player_display_name']:<22s} "
              f"{p['position']:<3s} {p['team']:<4s} val={p['value']:.2f}")
        i += 1
print("\nSaved final_board.csv")
