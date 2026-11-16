import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

print("=== 1. BIO (load_players) ===")
P = pl(nfl.load_players())
want = ["height", "weight", "college", "headshot",
        "birth", "draft", "years", "rookie", "jersey",
        "position", "status"]
cols = [c for c in P.columns
        if any(w in c.lower() for w in want)]
print("  rows %d" % len(P))
print("  matching cols: %s" % cols)
idc = [c for c in P.columns if "id" in c.lower()][:8]
print("  id cols: %s" % idc)

print("\n=== 2. WEEKLY STATS (for game logs + career) ===")
W = pl(nfl.load_player_stats(seasons=[2024, 2025]))
print("  rows %d | seasons %s"
      % (len(W), sorted(W["season"].unique())))
rec = [c for c in W.columns
       if any(w in c.lower() for w in
              ["target", "reception", "receiving",
               "carries", "rushing", "attempt",
               "completion", "passing", "sack",
               "fumble", "fantasy", "opponent"])]
print("  stat cols: %s" % rec[:26])

print("\n=== 3. SCHEDULE 2026 (weekly opponents) ===")
S = pl(nfl.load_schedules(seasons=[2026]))
print("  rows %d | cols %s"
      % (len(S), [c for c in S.columns][:12]))
print("  weeks %d to %d"
      % (S["week"].min(), S["week"].max()))

print("\n=== 4. stat_projections_2026 ===")
SP = pd.read_csv("stat_projections_2026.csv")
print("  rows %d" % len(SP))
print("  cols: %s" % list(SP.columns))
for p in ["QB", "RB", "WR", "TE"]:
    d = SP[SP["position"] == p]
    print("  %-3s n=%d" % (p, len(d)))

print("\n=== 5. BOARD COVERAGE ===")
B = pd.read_csv("board_final.csv", low_memory=False)
print("  board rows %d" % len(B))
ids = set(B["player_id"].astype(str))
pid = [c for c in P.columns
       if c.lower() in ("gsis_id", "player_id")]
if pid:
    hit = len(ids & set(P[pid[0]].astype(str)))
    print("  bio match on %s: %d of %d"
          % (pid[0], hit, len(ids)))
