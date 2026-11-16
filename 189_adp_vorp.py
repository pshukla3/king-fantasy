import json
import re
import pandas as pd

J = json.load(open("sleeper_proj_raw.json"))

def key(n):
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "",
               str(n).lower())
    return re.sub(r"[^a-z]", "", n)

rows = []
for d in J:
    p = d.get("player") or {}
    s = d.get("stats") or {}
    a = s.get("adp_ppr")
    if a is None or float(a) >= 900:
        continue
    nm = ((p.get("first_name") or "") + " "
          + (p.get("last_name") or "")).strip()
    rows.append({"k": key(nm), "sadp": float(a)})
A = pd.DataFrame(rows).sort_values("sadp")
A = A.drop_duplicates("k")
print("sleeper ADP available for %d players" % len(A))

B = pd.read_csv("board_final.csv", low_memory=False)
B["k"] = B["player_display_name"].apply(key)
had = int(pd.to_numeric(B["adp"], errors="coerce").notna().sum())
B = B.merge(A, on="k", how="left")
B["adp"] = pd.to_numeric(B["adp"], errors="coerce")
B["adp"] = B["adp"].fillna(B["sadp"])
now = int(B["adp"].notna().sum())
print("board ADP coverage: %d -> %d of %d"
      % (had, now, len(B)))
for p in ["QB", "RB", "WR", "TE"]:
    d = B[B["position"] == p]
    print("  %-4s %3d of %3d (%.0f%%)"
          % (p, int(d["adp"].notna().sum()), len(d),
             100.0 * d["adp"].notna().mean()))

B["pp"] = pd.to_numeric(B["points"], errors="coerce").fillna(0)
REPL = {"QB": 10, "RB": 30, "WR": 40, "TE": 12,
        "K": 10, "DST": 10, "DEF": 10}
print("\n=== REPLACEMENT LEVEL BY POSITION ===")
B["vorp"] = 0.0
for pos, n in REPL.items():
    m = B["position"].astype(str) == pos
    d = B.loc[m, "pp"].sort_values(ascending=False)
    if len(d) < n:
        continue
    base = float(d.iloc[n - 1])
    B.loc[m, "vorp"] = B.loc[m, "pp"] - base
    print("  %-4s %-6s = %.2f ppg" % (pos, "#%d" % n, base))

B = B.sort_values("vorp", ascending=False)
B = B.reset_index(drop=True)
B["rank"] = B.index + 1
B["pos_rank"] = B.groupby("position").cumcount() + 1
B = B.drop(columns=["k", "sadp"])
B.to_csv("board_final.csv", index=False)

print("\n=== TOP 24 BY VALUE OVER REPLACEMENT ===")
print("  %-3s %-22s %-4s %-4s %6s %6s %6s"
      % ("#", "player", "pos", "tm", "ppg", "vorp", "ADP"))
for _, r in B.head(24).iterrows():
    a = r["adp"]
    print("  %-3d %-22s %-4s %-4s %6.2f %+6.2f %6s"
          % (r["rank"], str(r["player_display_name"])[:22],
             str(r["position"])[:4], str(r["team"])[:4],
             r["pp"], r["vorp"],
             "--" if a != a else "%.1f" % a))

M = B[B["adp"].notna() & (B["pp"] > 0)].copy()
M["adp_rk"] = M["adp"].rank(method="min")
M["edge"] = M["adp_rk"] - M["rank"]
print("\n=== WE LIKE THESE MORE THAN THE MARKET ===")
print("  %-22s %-4s %6s %6s %7s"
      % ("player", "pos", "ours", "mkt", "edge"))
for _, r in M.nlargest(12, "edge").iterrows():
    print("  %-22s %-4s %6d %6.0f %+7.0f"
          % (str(r["player_display_name"])[:22],
             str(r["position"])[:4], r["rank"],
             r["adp_rk"], r["edge"]))
print("\n=== WE LIKE THESE LESS ===")
for _, r in M.nsmallest(12, "edge").iterrows():
    print("  %-22s %-4s %6d %6.0f %+7.0f"
          % (str(r["player_display_name"])[:22],
             str(r["position"])[:4], r["rank"],
             r["adp_rk"], r["edge"]))
