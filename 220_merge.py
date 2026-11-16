import re
import numpy as np
import pandas as pd

SUF = re.compile(r"\b(jr|sr|ii|iii|iv)\b")

def key(s):
    s = re.sub(r"[^a-z ]", " ", str(s).lower())
    return re.sub(r"\s+", "", SUF.sub(" ", s))

B = pd.read_csv("board_final.csv", low_memory=False)
V = pd.read_csv("proj_2026.csv")
R = pd.read_csv("rookie_proj_2026.csv")
B["k"] = B["player_display_name"].apply(key)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
R["k"] = R["nm"].apply(key)

print("=== SOURCES ===")
print("  board            %5d rows" % len(B))
print("  veterans (214)   %5d" % len(V))
print("  rookies  (219)   %5d" % len(R))

vid = set(V["player_id"].astype(str))
bid = set(B["player_id"].astype(str))
print("\n=== VETERAN MATCH (by player_id) ===")
print("  matched  %d of %d" % (len(vid & bid), len(V)))
mv = V[~V["player_id"].astype(str).isin(bid)]
if len(mv):
    print("  NOT ON BOARD:")
    for _, r in mv.head(8).iterrows():
        print("    %-24s %-3s %.2f"
              % (str(r["player_display_name"])[:24],
                 r["position"], r["proj"]))

BK = {}
for _, r in B.iterrows():
    BK.setdefault((r["k"], str(r["position"])), []).append(1)
R["hit"] = [(a, b) in BK for a, b in zip(R["k"], R["ps"])]
print("\n=== ROOKIE MATCH (name + position) ===")
print("  matched  %d of %d" % (int(R["hit"].sum()), len(R)))
mr = R[~R["hit"]]
if len(mr):
    print("  NOT ON BOARD (top 8 by proj):")
    for _, r in mr.nlargest(8, "proj").iterrows():
        print("    %-24s %-3s %-4s %.2f"
              % (str(r["nm"])[:24], r["ps"], r["tm"],
                 r["proj"]))

skill = B[B["position"].isin(["RB", "WR", "TE"])]
cov = len(vid & bid) + int(R["hit"].sum())
print("\n=== COVERAGE ===")
print("  RB/WR/TE rows on board : %d" % len(skill))
print("  covered by new model   : %d (%.0f%%)"
      % (cov, 100.0 * cov / len(skill)))
print("  left on OLD numbers    : %d" % (len(skill) - cov))
print("\n  QB stays on the 147 model, K/DST on 202/203.")
print("  nothing written yet - block B applies it.")

print("\n" + "=" * 58)
print("=== APPLYING ===")
DEAD = {"IR", "OUT", "OUT_SEASON", "PUP", "NFI"}
st = B["status"].astype(str).str.upper()
noteam = (B["team"].isna()
          | B["team"].astype(str).isin(["nan", "", "--"]))
frozen = st.isin(DEAD) | noteam
print("  rows frozen (dead/no team): %d" % int(frozen.sum()))

for c in ["p10", "p50", "p90"]:
    if c not in B.columns:
        B[c] = np.nan
if "src" not in B.columns:
    B["src"] = pd.Series([None] * len(B), dtype=object)
VM = V.set_index(V["player_id"].astype(str))
nv = 0
for i in B.index:
    pid = str(B.at[i, "player_id"])
    if pid not in VM.index or frozen.at[i]:
        continue
    r = VM.loc[pid]
    if isinstance(r, pd.DataFrame):
        r = r.iloc[0]
    B.at[i, "points"] = round(float(r["proj"]), 2)
    for c in ["p10", "p50", "p90"]:
        B.at[i, c] = round(float(r[c]), 2)
    B.at[i, "src"] = "model214"
    nv += 1

RM = {}
for _, r in R[R["hit"]].iterrows():
    RM.setdefault((r["k"], r["ps"]), r)
nr = 0
for i in B.index:
    kk = (B.at[i, "k"], str(B.at[i, "position"]))
    if kk not in RM or frozen.at[i]:
        continue
    if B.at[i, "src"] == "model214":
        continue
    B.at[i, "points"] = round(float(RM[kk]["proj"]), 2)
    B.at[i, "src"] = "rookie219"
    nr += 1

print("  veterans written : %d" % nv)
print("  rookies  written : %d" % nr)
B["np"] = pd.to_numeric(B["points"], errors="coerce")
B["mv"] = B["np"] - B["pp"]
M = B[B["src"].notna() & B["mv"].notna()]
print("  mean absolute change: %.2f ppg"
      % M["mv"].abs().mean())

print("\n=== BIGGEST INCREASES ===")
for _, r in M.nlargest(8, "mv").iterrows():
    print("  %-24s %-3s %-4s %6.2f -> %6.2f  %+.2f  %s"
          % (str(r["player_display_name"])[:24],
             r["position"], str(r["team"])[:4],
             r["pp"], r["np"], r["mv"], r["src"]))
print("\n=== BIGGEST DECREASES ===")
for _, r in M.nsmallest(8, "mv").iterrows():
    print("  %-24s %-3s %-4s %6.2f -> %6.2f  %+.2f  %s"
          % (str(r["player_display_name"])[:24],
             r["position"], str(r["team"])[:4],
             r["pp"], r["np"], r["mv"], r["src"]))

print("\n=== FROZEN PLAYERS THE MODEL WANTED TO RAISE ===")
print("  these stay at zero - status overrides the model")
V2 = V.set_index(V["player_id"].astype(str))["proj"]
n = 0
for i in B[frozen].index:
    p = V2.get(str(B.at[i, "player_id"]))
    if p is None or float(p) < 5:
        continue
    n += 1
    print("  %-24s %-3s %-4s model %.2f  [%s]"
          % (str(B.at[i, "player_display_name"])[:24],
             B.at[i, "position"], str(B.at[i, "team"])[:4],
             float(p), str(B.at[i, "status"])))
if not n:
    print("  none")

B.drop(columns=["k", "pp", "np", "mv"]).to_csv(
    "board_final.csv", index=False)
print("\n  wrote board_final.csv (%d rows)" % len(B))
print("  NEXT: python3 188_rerank.py")
