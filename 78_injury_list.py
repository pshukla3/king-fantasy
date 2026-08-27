import pandas as pd, re
import nflreadpy as nfl

def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

R = nfl.load_rosters(seasons=[2026])
R = R.to_pandas() if hasattr(R, "to_pandas") else R
R.to_csv("rosters_2026_fresh.csv", index=False)
print("roster rows: %d  |  as of today" % len(R))

SC = next((c for c in ["status", "roster_status", "status_description_abbr"]
           if c in R.columns), None)
print("\n=== EVERY STATUS VALUE IN THE 2026 ROSTER FEED ===")
print(R[SC].value_counts(dropna=False).to_string())

for c in R.columns:
    if "status" in c.lower() or "injur" in c.lower():
        print("\n--- column '%s' ---" % c)
        print(R[c].value_counts(dropna=False).head(12).to_string())

ACTIVE = {"ACT", "Active", "ACTIVE", "A01"}
OUT = R[~R[SC].isin(ACTIVE)].copy()
SKILL = ["QB", "RB", "WR", "TE", "K"]

D = pd.read_csv("depth_latest.csv", low_memory=False)
D["pos_rank"] = pd.to_numeric(D["pos_rank"], errors="coerce")
dc = D[["gsis_id", "pos_abb", "pos_rank"]].dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
OUT = OUT.merge(dc, on="gsis_id", how="left")

try:
    B = pd.read_csv("board_situational.csv", low_memory=False)
    B = B[["player_id", "proj", "value", "rk"]].rename(columns={"player_id": "gsis_id"})
    OUT = OUT.merge(B, on="gsis_id", how="left")
except Exception:
    OUT["proj"] = None
    OUT["value"] = None
    OUT["rk"] = None

NM = next(c for c in ["full_name", "player_name", "football_name"] if c in OUT.columns)
OUT = OUT[["team", NM, "position", SC, "pos_abb", "pos_rank", "proj", "value", "rk"]]
OUT.columns = ["team", "player", "position", "status", "depth_pos", "depth_rank",
               "proj", "value", "board_rank"]
OUT = OUT.sort_values(["team", "position", "player"])
OUT.to_csv("injury_list_2026.csv", index=False)

print("\n\n%s" % ("=" * 78))
print("NON-ACTIVE PLAYERS, ALL 32 TEAMS  (%d total, %d at skill positions)"
      % (len(OUT), len(OUT[OUT["position"].isin(SKILL)])))
print("=" * 78)
for tm, x in OUT.groupby("team"):
    sk = x[x["position"].isin(SKILL)]
    print("\n--- %s  (%d total, %d skill) ---" % (tm, len(x), len(sk)))
    for _, r in x.iterrows():
        star = " *" if r["position"] in SKILL else "  "
        rk = "" if r["board_rank"] != r["board_rank"] else "  board #%d" % r["board_rank"]
        print("  %s%-24s %-4s %-6s%s" % (star, r["player"], r["position"], r["status"], rk))

print("\n\n=== FANTASY-RELEVANT ONLY (skill positions, sorted by what they were worth) ===")
sk = OUT[OUT["position"].isin(SKILL)].copy()
sk["value"] = pd.to_numeric(sk["value"], errors="coerce")
print(sk.sort_values("value", ascending=False).head(40).to_string(index=False))
print("\nSaved injury_list_2026.csv and rosters_2026_fresh.csv")
