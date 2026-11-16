import json
import re
import pandas as pd

def key(n):
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "",
               str(n).lower())
    return re.sub(r"[^a-z]", "", n)

J = json.load(open("sleeper_proj_raw.json"))
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
S = pd.DataFrame(rows).sort_values("sadp")
S = S.drop_duplicates("k")

E = pd.read_csv("espn_adp_2026.csv")
E["k"] = E["nm"].apply(key)
E = E.sort_values("eadp").drop_duplicates("k")[["k", "eadp"]]
print("sleeper adp %d | espn adp %d" % (len(S), len(E)))

C = S.merge(E, on="k", how="inner")
print("\n=== DO THE TWO SOURCES AGREE? ===")
print("  overlap %d players" % len(C))
print("  correlation r = %.3f" % C["sadp"].corr(C["eadp"]))
C["d"] = C["sadp"] - C["eadp"]
print("  mean |diff| = %.1f picks" % C["d"].abs().mean())

B = pd.read_csv("board_final.csv", low_memory=False)
B["k"] = B["player_display_name"].apply(key)
B = B.merge(S, on="k", how="left").merge(
    E, on="k", how="left")

print("\n=== BIGGEST SOURCE DISAGREEMENTS ===")
D = B[B["sadp"].notna() & B["eadp"].notna()].copy()
D["d"] = D["sadp"] - D["eadp"]
print("  %-22s %-4s %7s %7s %7s"
      % ("player", "pos", "sleepr", "espn", "diff"))
for _, r in D.reindex(
        D["d"].abs().sort_values(
            ascending=False).index).head(10).iterrows():
    print("  %-22s %-4s %7.1f %7.1f %+7.1f"
          % (str(r["player_display_name"])[:22],
             str(r["position"])[:4], r["sadp"],
             r["eadp"], r["d"]))

B["adp"] = B[["sadp", "eadp"]].mean(axis=1, skipna=True)
print("\n=== CONSENSUS ADP COVERAGE ===")
for p in ["QB", "RB", "WR", "TE", "K", "DST"]:
    d = B[B["position"] == p]
    if not len(d):
        continue
    print("  %-4s %3d of %3d (%.0f%%)"
          % (p, int(d["adp"].notna().sum()), len(d),
             100.0 * d["adp"].notna().mean()))

B["pp"] = pd.to_numeric(B["points"],
                        errors="coerce").fillna(0)
REPL = {"QB": 10, "RB": 30, "WR": 40, "TE": 12,
        "K": 10, "DST": 10, "DEF": 10}
B["vorp"] = 0.0
for pos, n in REPL.items():
    m = B["position"].astype(str) == pos
    d = B.loc[m, "pp"].sort_values(ascending=False)
    if len(d) < n:
        continue
    B.loc[m, "vorp"] = B.loc[m, "pp"] - float(d.iloc[n - 1])

LATE = B["position"].astype(str).isin(["K", "DST", "DEF"])
B["sortk"] = B["vorp"]
B.loc[LATE, "sortk"] = B.loc[LATE, "vorp"] - 100.0
B.loc[B["pp"] <= 0, "sortk"] = B["vorp"] - 1000.0
print("\n  K/DST pushed below all healthy skill players")
print("  zeroed players pushed to the very bottom")

try:
    BY = pd.read_csv("byes_2026.csv")
    BY["team"] = BY["team"].astype(str).replace(
        {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
         "JAC": "JAX"})
    BYE = dict(zip(BY["team"], BY["bye"]))
except Exception:
    BYE = {}
B["bye"] = B["team"].astype(str).map(BYE).fillna(0)
B["bye"] = pd.to_numeric(B["bye"],
                         errors="coerce").fillna(0).astype(int)
print("  bye weeks attached for %d of %d rows"
      % (int((B["bye"] > 0).sum()), len(B)))

B = B.sort_values("sortk", ascending=False)
B = B.reset_index(drop=True)
B["rank"] = B.index + 1
B["pos_rank"] = B.groupby("position").cumcount() + 1
B["season_pts"] = (B["pp"] * 17.0).round(1)
B = B.drop(columns=["k", "sortk"])
B.to_csv("board_final.csv", index=False)

print("\n=== TOP 25 ===")
print("  %-3s %-24s %-6s %4s %7s %7s %7s"
      % ("RK", "player", "pos", "bye", "ppg", "x17", "ADP"))
for _, r in B.head(25).iterrows():
    a = r["adp"]
    print("  %-3d %-24s %-6s %4s %7.2f %7.0f %7s"
          % (r["rank"],
             "%s (%s)" % (str(r["player_display_name"])[:17],
                          str(r["team"])[:3]),
             "%s%d" % (r["position"], r["pos_rank"]),
             r["bye"] if r["bye"] else "--",
             r["pp"], r["pp"] * 17,
             "--" if a != a else "%.1f" % a))

print("\n=== WHERE DO K AND DST LAND NOW? ===")
for p in ["K", "DST"]:
    d = B[B["position"] == p]
    if len(d):
        print("  best %-4s is overall #%d"
              % (p, int(d["rank"].min())))
