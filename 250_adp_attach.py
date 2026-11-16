import json
import re
import pandas as pd

def key(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

J = json.load(open("sleeper_proj_raw.json"))
rows = []
for d in J:
    p = d.get("player") or {}
    st = d.get("stats") or {}
    a = st.get("adp_ppr")
    if a is None or float(a) >= 999:
        continue
    nm = (str(p.get("first_name", "")) + " "
          + str(p.get("last_name", ""))).strip()
    rows.append({"k": key(nm),
                 "position": p.get("position"),
                 "sadp": float(a)})
A = pd.DataFrame(rows).sort_values("sadp")
A = A.drop_duplicates(["k", "position"])
print("sleeper adp rows usable: %d" % len(A))

B = pd.read_csv("board_final.csv", low_memory=False)
B["k"] = B["player_display_name"].apply(key)
before = int(pd.to_numeric(
    B["adp"], errors="coerce").notna().sum())
B = B.merge(A, on=["k", "position"], how="left")
B["adp"] = pd.to_numeric(B["adp"], errors="coerce")
B["adp"] = B["adp"].fillna(B["sadp"])
after = int(B["adp"].notna().sum())
print("adp coverage %d -> %d of %d"
      % (before, after, len(B)))
for p in ["QB", "RB", "WR", "TE", "K", "DST"]:
    d = B[B["position"] == p]
    print("  %-4s %4d rows | %4d adp"
          % (p, len(d), int(d["adp"].notna().sum())))
z = B[pd.to_numeric(B["points"],
                    errors="coerce").fillna(0) > 0]
print("\n  live players still without adp: %d"
      % int(z["adp"].isna().sum()))
B.drop(columns=["k", "sadp"]).to_csv(
    "board_final.csv", index=False)
print("wrote board_final.csv - points untouched")
