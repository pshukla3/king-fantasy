import json
import pandas as pd

M = json.load(open("pos_mult.json"))
print("positional multipliers:", M)

B = pd.read_csv("board_final.csv")
if "vorp_raw" not in B.columns:
    B["vorp_raw"] = B["vorp"]
B["vorp"] = (B["vorp_raw"]
             * B["position"].map(
                 lambda p: float(M.get(str(p), 1.0)))
             ).round(2)
B = B.sort_values("vorp", ascending=False)
B["rank_v"] = range(1, len(B) + 1)
B.to_csv("board_final.csv", index=False)

print("\n=== TOP 20 AFTER POSITIONAL SCALING ===")
print("%-3s %-24s %-4s %7s %7s %7s"
      % ("#", "PLAYER", "POS", "PROJ", "RAW", "VALUE"))
for _, r in B.head(20).iterrows():
    print("%-3d %-24s %-4s %7.2f %7.2f %7.2f"
          % (r["rank_v"], r["player_display_name"][:24],
             r["position"],
             r.get("proj_sch", r["points"]),
             r["vorp_raw"], r["vorp"]))

print("\n=== FIRST PLAYER AT EACH POSITION ===")
for p in ("RB", "WR", "TE", "QB", "K", "DST"):
    z = B[B["position"] == p].head(1)
    for _, r in z.iterrows():
        print("  %-4s #%-4d %-24s value %.2f"
              % (p, r["rank_v"],
                 r["player_display_name"][:24], r["vorp"]))
