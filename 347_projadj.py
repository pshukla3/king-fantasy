import json, re
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

M = json.load(open("inj_mult.json"))
BYT = M.get("by_type", {})
_q = M.get("status", {}).get("Questionable", {})
QBASE = float(_q.get("exp", 0.515))
QRATIO = float(_q.get("ratio", 0.906))
ZERO = {"out", "doubtful", "injured reserve", "ir",
        "suspension", "suspended",
        "physically unable to perform", "pup",
        "non football injury"}
INJ = json.load(open("site/_inj.json"))
print("Questionable unresolved=%.3f | if cleared=%.3f"
      % (QBASE, QRATIO))
for k, v in BYT.items():
    print("  %-10s unresolved %.3f | if plays %.3f"
          % (k, v["exp"], v["ratio"]))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B["points"] = pd.to_numeric(B["points"], errors="coerce")

def mult(k):
    j = INJ.get(k)
    if not j:
        return 1.0, "", ""
    st = str(j.get("status") or "").strip()
    ty = str(j.get("type") or "").strip()
    if st.lower() in ZERO:
        return 0.0, st, ty
    ent = None
    for t, v in BYT.items():
        if t and t.lower() in ty.lower():
            ent = v
            break
    if st.lower() == "questionable":
        # unresolved: expected value includes the
        # chance he does not suit up at all
        return (float(ent["exp"]) if ent
                else float(QBASE)), st, ty
    if st.lower() == "active" and ty:
        # cleared to play - the coin flip is settled,
        # so only the measured performance hit applies
        return (float(ent["ratio"]) if ent
                else float(QRATIO)), st, ty
    return 1.0, st, ty

rows = B["k"].map(mult)
B["inj_mult"] = [r[0] for r in rows]
B["inj_status"] = [r[1] for r in rows]
B["inj_type"] = [r[2] for r in rows]
B["proj_adj"] = (B["points"] * B["inj_mult"]).round(2)

hit = B[B["inj_mult"] < 1.0].sort_values("points",
                                         ascending=False)
print("\n%d players adjusted | %d zeroed"
      % (len(hit), int((B["inj_mult"] == 0).sum()))) 
print("\n%-24s %-4s %-14s %-11s %6s %6s"
      % ("PLAYER", "POS", "STATUS", "TYPE", "PROJ", "ADJ"))
print("-" * 70)
for _, r in hit.head(25).iterrows():
    print("%-24s %-4s %-14s %-11s %6.2f %6.2f"
          % (str(r["player_display_name"])[:24], r["position"],
             r["inj_status"][:14], str(r["inj_type"])[:11],
             r["points"], r["proj_adj"]))

B.drop(columns=["k"]).to_csv("board_final.csv", index=False)
out = {r["k"]: {"adj": float(r["proj_adj"]),
                "m": float(r["inj_mult"]),
                "st": r["inj_status"], "ty": r["inj_type"]}
       for _, r in B.iterrows()
       if pd.notna(r["proj_adj"]) and r["inj_mult"] < 1.0}
json.dump(out, open("site/_projadj.json", "w"))
print("\nwrote proj_adj to board_final.csv "
      "and site/_projadj.json (%d entries)" % len(out))
