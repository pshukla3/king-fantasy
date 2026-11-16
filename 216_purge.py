import json
import re
import pandas as pd

SUF = re.compile(r"\b(jr|sr|ii|iii|iv)\b")

def key(s):
    s = re.sub(r"[^a-z ]", " ", str(s).lower())
    s = SUF.sub(" ", s)
    return re.sub(r"\s+", "", s)

PJ = json.load(open("sleeper_players_fresh.json"))
IDX, IDX2 = {}, {}
for d in PJ.values():
    nm, ps = d.get("full_name"), d.get("position")
    if not nm or not ps:
        continue
    IDX.setdefault((key(nm), str(ps)), d)
    IDX2.setdefault(key(nm), d)

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")

rows = []
for _, r in B.iterrows():
    ps = str(r["position"])
    if ps in ("DST", "DEF"):
        continue
    k = key(r["player_display_name"])
    d = IDX.get((k, ps)) or IDX2.get(k)
    tm = (d or {}).get("team")
    if d is None:
        f = "NOT IN FEED"
    elif not tm:
        f = "NO TEAM"
    else:
        f = ""
    rows.append({"pid": r["player_id"],
                 "nm": r["player_display_name"],
                 "ps": ps, "ours": str(r["team"]),
                 "live": tm or "", "flag": f,
                 "ppg": r["pp"]})

A = pd.DataFrame(rows)
A.to_csv("roster_audit_v2.csv", index=False)
print("skill rows: %d" % len(A))
print(A["flag"].value_counts().to_string())
print("\n  suffix fix recovered: %d rows"
      % (38 - int((A["flag"] == "NOT IN FEED").sum())))

d = A[(A["flag"] != "") & (A["ppg"].fillna(0) > 3)]
print("\n=== STILL DEAD, WITH A PROJECTION ===")
print("  %-24s %-4s %-5s %-13s %6s"
      % ("player", "pos", "ours", "flag", "ppg"))
for _, r in d.sort_values("ppg", ascending=False).head(30).iterrows():
    print("  %-24s %-4s %-5s %-13s %6.2f"
          % (str(r["nm"])[:24], r["ps"], r["ours"],
             r["flag"], r["ppg"]))
print("\n  dead rows above 3 ppg: %d" % len(d))

print("\n" + "=" * 58)
print("=== APPLYING THE PURGE ===")
DEAD = set(A[A["flag"] == "NO TEAM"]["pid"])
FIX = dict(zip(A[A["flag"] == ""]["pid"],
               A[A["flag"] == ""]["live"]))
TMFIX = {"LAR": "LA", "WSH": "WAS", "JAC": "JAX",
         "AZ": "ARI"}

n_junk = int(B["player_display_name"].astype(str)
             .str.contains("Duplicate Player",
                           na=False).sum())
B = B[~B["player_display_name"].astype(str)
      .str.contains("Duplicate Player", na=False)].copy()
print("  dropped junk rows: %d" % n_junk)

m = B["player_id"].isin(DEAD)
lost = float(B.loc[m, "pp"].fillna(0).sum())
B.loc[m, "points"] = 0.0
B.loc[m, "status"] = "NO_TEAM"
print("  zeroed no-team rows: %d (%.0f ppg removed)"
      % (int(m.sum()), lost))

nfix = 0
for i in B.index:
    v = FIX.get(B.at[i, "player_id"])
    if not v:
        continue
    v = TMFIX.get(v, v)
    if str(B.at[i, "team"]) != v:
        B.at[i, "team"] = v
        nfix += 1
print("  corrected team assignments: %d" % nfix)

B.to_csv("board_final.csv", index=False)
print("\n  board now %d rows" % len(B))
print("  zero-ppg rows: %d"
      % int((pd.to_numeric(B["points"], errors="coerce")
             .fillna(0) == 0).sum()))
print("\n  NOTE: 188_rerank.py must run after this to")
print("  re-sort and push the zeroed rows to the bottom.")
