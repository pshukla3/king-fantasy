import pandas as pd
import numpy as np
import json
import re

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
A = pd.DataFrame(rows)
A = A.sort_values("sadp").drop_duplicates(
    ["k", "position"])
print("sleeper ADP rows usable: %d" % len(A))

B = pd.read_csv("board_final.csv", low_memory=False)
B["k"] = B["player_display_name"].apply(key)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
B = B.merge(A, on=["k", "position"], how="left")
print("board %d rows | with sleeper ADP %d"
      % (len(B), int(B["sadp"].notna().sum())))
for p in ["QB", "RB", "WR", "TE"]:
    d = B[B["position"] == p]
    print("  %-4s %4d rows | %4d with ADP"
          % (p, len(d), int(d["sadp"].notna().sum())))

POS = ["QB", "RB", "WR", "TE"]

def reslot(w):
    """w = weight on the MODEL. 1.0 = pure model,
    0.0 = pure ADP order. Returns pid -> new ppg."""
    out = {}
    for p in POS:
        d = B[(B["position"] == p)
              & (B["pp"] > 0)
              & B["sadp"].notna()].copy()
        if len(d) < 5:
            continue
        d = d.sort_values("pp", ascending=False)
        d["mr"] = np.arange(1, len(d) + 1)
        d = d.sort_values("sadp")
        d["ar"] = np.arange(1, len(d) + 1)
        d["br"] = w * d["mr"] + (1 - w) * d["ar"]
        curve = np.sort(d["pp"].values)[::-1]
        d = d.sort_values(["br", "mr"])
        for i, (_, r) in enumerate(d.iterrows()):
            out[(r["k"], p)] = float(curve[i])
    return out

WHO = ["Ja'Marr Chase", "Puka Nacua",
       "Jaxon Smith-Njigba", "Justin Jefferson",
       "Wan'Dale Robinson", "CeeDee Lamb",
       "Malik Nabers", "Amon-Ra St. Brown"]

print("\n=== WR ORDER AT EACH BLEND WEIGHT ===")
print("  w=1.0 pure model | w=0.0 pure Sleeper ADP\n")
for w in [1.0, 0.6, 0.4, 0.0]:
    M = reslot(w)
    d = B[(B["position"] == "WR") & (B["pp"] > 0)
          & B["sadp"].notna()].copy()
    d["nw"] = [M.get((k, "WR"), np.nan)
               for k in d["k"]]
    d = d.sort_values("nw", ascending=False)
    d = d.reset_index(drop=True)
    print("  --- w = %.1f ---" % w)
    for i, r in d.head(8).iterrows():
        print("    WR%-2d %-22s %6.2f  adp %5.1f"
              % (i + 1,
                 str(r["player_display_name"])[:22],
                 r["nw"], r["sadp"]))
    print()

print("=== THE PLAYERS YOU NAMED, ACROSS WEIGHTS ===")
print("  %-22s %6s %6s %6s %6s %6s"
      % ("player", "adp", "w1.0", "w0.6", "w0.4", "w0.0"))
print("  " + "-" * 58)
CACHE = {w: reslot(w) for w in [1.0, 0.6, 0.4, 0.0]}
for nm in WHO:
    h = B[B["player_display_name"].astype(str)
          == nm]
    if not len(h):
        print("  %-22s not found" % nm[:22])
        continue
    r = h.iloc[0]
    k, p = r["k"], r["position"]
    vals = []
    for w in [1.0, 0.6, 0.4, 0.0]:
        d = B[(B["position"] == p) & (B["pp"] > 0)
              & B["sadp"].notna()].copy()
        d["nw"] = [CACHE[w].get((x, p), np.nan)
                   for x in d["k"]]
        d = d.sort_values("nw", ascending=False)
        d = d.reset_index(drop=True)
        i = d.index[d["k"] == k]
        vals.append(int(i[0]) + 1 if len(i) else 0)
    print("  %-22s %6.1f %6s %6s %6s %6s"
          % (nm[:22], r["sadp"],
             "%s%d" % (p, vals[0]),
             "%s%d" % (p, vals[1]),
             "%s%d" % (p, vals[2]),
             "%s%d" % (p, vals[3])))

print("\n  the point-per-slot curve NEVER changes.")
print("  WR1 pays whatever the model measured WR1")
print("  pays. only who sits in the slot moves.")
