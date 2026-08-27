import pandas as pd, json, re, os

def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

if not os.path.exists("injuries_2026.csv"):
    seed = [
        ("Ricky Pearsall", "SF", "WR", "OUT", "Knee", "PCL surgery, placed on IR"),
        ("Jayden Higgins", "HOU", "WR", "OUT", "Knee", "torn ACL, out for the season"),
        ("George Kittle", "SF", "TE", "PUP", "Achilles", "torn Achilles Jan 11, opened camp on PUP"),
        ("Sam LaPorta", "DET", "TE", "QUESTIONABLE", "Hip", "hip; missed most of 2025 after back surgery"),
        ("Tyler Warren", "IND", "TE", "QUESTIONABLE", "Groin", "groin, expected back within a week"),
        ("Luther Burden III", "CHI", "WR", "QUESTIONABLE", "Groin", "groin, likely misses the preseason"),
    ]
    pd.DataFrame(seed, columns=["player", "team", "pos", "status", "injury", "note"]).to_csv(
        "injuries_2026.csv", index=False)
    print("created injuries_2026.csv - add a row per injury, the UI reads it live")

I = pd.read_csv("injuries_2026.csv").fillna("")
EF = pd.read_csv("injury_effects.csv")
EF["k_"] = EF["inj"].map(norm)
D = pd.read_csv("depth_latest.csv", low_memory=False)
D["k_"] = D["player_name"].map(norm)

with open("ui_data.json") as f:
    U = json.load(f)
for t in U["teams"]:
    U["teams"][t]["injuries"] = []

print("\n=== 2026 INJURY LIST + MEASURED TIMELINE ===")
print("  timeline comes from %d historical injury spells (script 54)" % EF["n"].sum())
print("  " + "-" * 78)
hit = 0
for _, r in I.iterrows():
    k = norm(r["player"])
    m = D[D["k_"] == k]
    if not len(m):
        m = D[D["k_"].str.contains(k, na=False)]
    gid = m.iloc[0]["gsis_id"] if len(m) else ""
    tm = m.iloc[0]["team"] if len(m) else r["team"]

    e = EF[EF["k_"] == norm(r["injury"])]
    tl, desc = "", ""
    if len(e):
        e = e.iloc[0]
        med, p75, n = e["med_out"], e["p75_out"], int(e["n"])
        ret = e["ret_pct"] if e["ret_pct"] == e["ret_pct"] else None
        nxt = e["nxt_pct"] if e["nxt_pct"] == e["nxt_pct"] else None
        tl = "%.0f wk typical, %.0f wk if it lingers" % (med, p75)
        parts = ["across %d past cases of this injury" % n]
        if ret is not None:
            parts.append("returns at %.0f%% of prior scoring for 4 games" % (100 * ret))
        if nxt is not None:
            parts.append("%.0f%% of prior scoring the following season" % (100 * nxt))
        desc = "; ".join(parts)
    if str(r["status"]).upper() == "OUT":
        tl = "out for the season"
        desc = desc or "no return expected in 2026"

    rec = {"id": gid, "name": r["player"], "pos": r["pos"], "status": str(r["status"]).upper(),
           "inj": r["injury"], "note": r["note"], "timeline": tl, "desc": desc}
    if tm in U["teams"]:
        U["teams"][tm]["injuries"].append(rec)
        hit += 1
    if gid and gid in U["players"]:
        U["players"][gid]["injury"] = rec
    print("  %-20s %-4s %-14s %-11s %s" % (r["player"], tm, r["injury"], r["status"], tl))

with open("ui_data.json", "w") as f:
    json.dump(U, f)
print("\n  %d of %d matched to a depth chart" % (hit, len(I)))
print("Updated ui_data.json")
