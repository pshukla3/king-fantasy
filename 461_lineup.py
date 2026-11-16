import json, re, numpy as np
import nflreadpy as nfl

WK, MYID = 3, 1
def norm(s):
    s = str(s or "").lower(); s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

P = json.load(open("site/_projweek.json"))
SL = json.load(open("site/_slteams.json"))
INJ = json.load(open("site/_inj.json"))
B = {norm(r["n"]): r for r in
     json.load(open("site/_board.json"))["rows"]}
IBY = {}
for v in INJ.values():
    IBY[norm(v.get("n"))] = v

me = next(t for t in SL["teams"] if int(t["id"]) == MYID)
print("=== %s  (week %d) ===\n" % (me["owner"], WK))

d = nfl.load_player_stats(seasons=[2026]).to_pandas()
tc = "team" if "team" in d.columns else "recent_team"
d["tgt"] = d.get("targets", 0); d["car"] = d.get("carries", 0)
d["rec"] = d.get("receptions", 0)
tv = (d.groupby(["week", tc]).agg(t_tgt=("tgt", "sum"),
                                  t_car=("car", "sum"))
      .reset_index())
d = d.merge(tv, on=["week", tc], how="left")

# who on each team is hurt, and what share do they vacate
VAC = {}
for _, r in d.iterrows():
    k = norm(r["player_display_name"])
    iv = IBY.get(k)
    if not iv:
        continue
    st = str(iv.get("status") or "")
    if st.startswith("Active") or not st:
        continue
    p_out = {"Out": 1.0, "IR": 1.0, "PUP": 1.0,
             "Doubt": 0.85, "Quest": 0.25}
    frac = 0.0
    for kk, vv in p_out.items():
        if st.startswith(kk):
            frac = vv
            break
    if frac <= 0 or not r["t_tgt"]:
        continue
    tm = r[tc]
    share = r["tgt"] / max(r["t_tgt"], 1)
    VAC.setdefault(tm, {"share": 0.0, "who": []})
    VAC[tm]["share"] += share * frac / 2.0   # per-game avg
    if k not in [x[0] for x in VAC[tm]["who"]]:
        VAC[tm]["who"].append((k, iv.get("n"), st,
                               round(share, 3)))

print("=== vacated target share by team ===")
for tm, v in sorted(VAC.items(),
                    key=lambda x: -x[1]["share"])[:10]:
    if v["share"] < 0.03:
        continue
    print("  %-4s  %.1f%% of targets vacated" 
          % (tm, 100 * v["share"]))
    for _, nm, st, sh in v["who"]:
        print("        %-22s %-14s was %.0f%% of targets"
              % (nm, st, 100 * sh))

print("\n=== your roster, week %d ===" % WK)
print("  %-22s %-4s %-4s %6s %6s %6s  %s"
      % ("PLAYER", "POS", "TM", "PROJ", "ADJ", "L2 PPG",
         "NOTE"))
rows = []
for p in me["players"]:
    k = p.get("k") or norm(p["n"])
    v = P.get(k)
    proj = 0.0
    if v:
        proj = next((x["m"] for x in v["wk"]
                     if x["w"] == WK), 0.0)
    g = d[d["player_display_name"].apply(norm) == k]
    l2 = []
    for _, r in g.iterrows():
        pts = (r["rec"] * 1 + (r.get("receiving_yards") or 0) * .1
               + (r.get("receiving_tds") or 0) * 6
               + (r.get("rushing_yards") or 0) * .1
               + (r.get("rushing_tds") or 0) * 6
               + (r.get("passing_yards") or 0) * .04
               + (r.get("passing_tds") or 0) * 4)
        l2.append(pts)
    ppg = float(np.mean(l2)) if l2 else 0.0
    tgts = float(g["tgt"].mean()) if len(g) else 0.0

    note = ""
    iv = IBY.get(k)
    if iv and iv.get("status") and \
            not str(iv["status"]).startswith("Active"):
        note = "%s (%s)" % (iv["status"], iv.get("type") or "")
    adj = proj
    tm = p.get("tm")
    vc = VAC.get(tm)
    if vc and vc["share"] > 0.03 and p["pos"] in ("WR", "TE"):
        # absorb vacated share in proportion to current role
        own = tgts / max(float(g["t_tgt"].mean()) if len(g)
                         else 30, 1)
        boost = 1 + (vc["share"] * min(1.0, own * 3))
        adj = proj * boost
        note = (note + "  " if note else "") + \
            "+%.0f%% vacated targets" % (100 * (boost - 1))
    rows.append({"p": p, "proj": proj, "adj": adj,
                 "ppg": ppg, "tgt": tgts, "note": note})

for r in sorted(rows, key=lambda x: -x["adj"]):
    p = r["p"]
    print("  %-22s %-4s %-4s %6.1f %6.1f %6.1f  %s"
          % (p["n"][:22], p["pos"], p["tm"], r["proj"],
             r["adj"], r["ppg"], r["note"]))
json.dump({norm(r["p"]["n"]): round(r["adj"], 2)
           for r in rows}, open("wk_adj_lineup.json", "w"))

# optimal lineup on adjusted numbers
SLOTS = [s for s in SL["slots"] if s not in ("BN", "IR")]
EL = {"QB": ["QB"], "RB": ["RB"], "WR": ["WR"], "TE": ["TE"],
      "K": ["K"], "DEF": ["DEF", "DST"],
      "FLEX": ["RB", "WR", "TE"]}
pool = sorted(rows, key=lambda x: -x["adj"])
used, out, flex = set(), [], []
for s in SLOTS:
    if "FLEX" in s:
        flex.append(s); continue
    for r in pool:
        if r["p"]["pid"] in used: continue
        if r["p"]["pos"] in EL.get(s, []):
            used.add(r["p"]["pid"]); out.append((s, r)); break
for s in flex:
    for r in pool:
        if r["p"]["pid"] in used: continue
        if r["p"]["pos"] in EL.get(s, []):
            used.add(r["p"]["pid"]); out.append((s, r)); break

print("\n=== RECOMMENDED LINEUP ===")
tot = 0
for s, r in out:
    tot += r["adj"]
    print("  %-6s %-22s %6.1f  %s"
          % (s, r["p"]["n"][:22], r["adj"], r["note"]))
print("  %-6s %-22s %6.1f" % ("", "TOTAL", tot))
print("\n=== on your bench ===")
for r in pool:
    if r["p"]["pid"] not in used:
        print("  %-22s %-4s %6.1f  %s"
              % (r["p"]["n"][:22], r["p"]["pos"],
                 r["adj"], r["note"]))
