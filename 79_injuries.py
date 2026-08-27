import pandas as pd, json, re

TEAMFIX = {"AZ": "ARI", "LAR": "LA", "JAC": "JAX", "WSH": "WAS"}
def tfix(t):
    t = str(t).upper().strip()
    return TEAMFIX.get(t, t)

def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

I = pd.read_csv("injuries_2026.csv")
I["team"] = I["team"].map(tfix)
for _c in ["gmult_override", "pmult_override"]:
    if _c not in I.columns:
        I[_c] = float("nan")

for _c in ["weeks_out", "kind", "note"]:
    if _c not in I.columns:
        print("  !! injuries_2026.csv is missing column '%s' - old schema, rewrite it" % _c)
        I[_c] = float("nan") if _c == "weeks_out" else ""

print("injury rows: %d  |  skill positions: %d"
      % (len(I), int(I["pos"].isin(["QB", "RB", "WR", "TE", "K"]).sum())))

E = pd.read_csv("injury_effects.csv")
E["key"] = E["inj"].map(norm)
ACHILLES = {"n": 5, "med_out": 1.0, "p75_out": 2.0, "ret_pct": None, "nxt_pct": 0.66}

D = pd.read_csv("depth_latest.csv", low_memory=False)
D["k_"] = D["player_name"].map(norm)
DC = D.dropna(subset=["gsis_id"]).drop_duplicates("k_").set_index("k_")

U = json.load(open("ui_data.json"))
for t in U["teams"]:
    U["teams"][t]["injuries"] = []

def effect(inj):
    k = norm(inj)
    if "achilles" in k:
        return ACHILLES
    h = E[E["key"] == k]
    if not len(h):
        return None
    r = h.iloc[0]
    return {"n": int(r["n"]), "med_out": float(r["med_out"]),
            "p75_out": float(r["p75_out"]), "ret_pct": float(r["ret_pct"]),
            "nxt_pct": float(r["nxt_pct"])}

rows, hit = [], 0
for _, r in I.iterrows():
    st, inj = str(r["status"]).upper(), str(r["injury"])
    e = effect(inj)
    wk, basis = None, ""

    if st in ("OUT_SEASON", "IR"):
        wk, basis = 17.0, "season-ending"
    elif r["weeks_out"] == r["weeks_out"]:
        wk, basis = float(r["weeks_out"]), "reported timeline"
    elif st in ("PUP", "NFI") and e:
        wk, basis = e["p75_out"], "p75 of %d past cases (CHOSEN not measured)" % e["n"]
    elif st in ("PUP", "NFI"):
        wk, basis = 3.0, "PUP default (INVENTED - no injury named)"
    elif e:
        wk, basis = e["med_out"], "median of %d past cases" % e["n"]
    else:
        wk, basis = 0.0, "no measured comparable"

    gmult = max(0.0, min(1.0, (17.0 - wk) / 17.0))

    pmult, pbasis = 1.0, ""
    if st in ("OUT_SEASON", "IR"):
        pmult = 0.0
    elif e and str(r["kind"]) == "carryover" and e["nxt_pct"]:
        pmult = e["nxt_pct"]
        pbasis = "next-season scoring ratio, n=%d" % e["n"]
    elif e and e["ret_pct"]:
        g = max(1.0, 17.0 - wk)
        back = min(4.0, g)
        pmult = (back * e["ret_pct"] + (g - back)) / g
        pbasis = "first-4-games-back ratio %.2f, n=%d" % (e["ret_pct"], e["n"])

    if st in ("OUT_SEASON", "IR"):
        tl = "out for the season"
    elif wk >= 1:
        tl = "%.0f wk%s expected out" % (wk, "" if wk < 2 else "s")
    else:
        tl = "no games expected missed"

    gid = ""
    k = norm(r["player"])
    for cand in DC.index:
        if cand == k or (len(k) > 8 and k in cand) or (len(cand) > 8 and cand in k):
            gid = DC.loc[cand, "gsis_id"]
            break

    rec = {"id": gid, "name": r["player"], "pos": r["pos"], "status": st,
           "inj": inj, "note": "" if r["note"] != r["note"] else str(r["note"]),
           "timeline": tl, "games_mult": round(gmult, 3),
           "points_mult": round(pmult, 3),
           "desc": ("%s; %s" % (basis, pbasis)).strip("; ")}
    tm = r["team"]
    if tm in U["teams"]:
        U["teams"][tm]["injuries"].append(rec)
        hit += 1
    if gid and gid in U["players"]:
        U["players"][gid]["injury"] = rec
    rows.append({**rec, "team": tm, "weeks_out": wk})

O = pd.DataFrame(rows)
O[["player" if False else "name", "team", "pos", "status", "inj", "weeks_out",
   "games_mult", "points_mult", "timeline", "desc"]].rename(
    columns={"name": "player"}).to_csv("news_overrides_v3.csv", index=False)

json.dump(U, open("ui_data.json", "w"))

SK = O[O["pos"].isin(["QB", "RB", "WR", "TE", "K"])].copy()
print("\n%s" % ("=" * 100))
print("FANTASY-RELEVANT INJURIES  (%d of %d rows)" % (len(SK), len(O)))
print("=" * 100)
print("  %-24s %-4s %-3s %-12s %-11s %5s %6s  %s"
      % ("player", "tm", "pos", "status", "injury", "gMlt", "pMlt", "basis"))
print("  " + "-" * 98)
for _, r in SK.sort_values(["games_mult", "points_mult"]).iterrows():
    print("  %-24s %-4s %-3s %-12s %-11s %5.2f %6.2f  %s"
          % (r["name"][:24], r["team"], r["pos"], r["status"], r["inj"][:11],
             r["games_mult"], r["points_mult"], r["desc"][:44]))

print("\n\n=== HOW MANY MATCHED TO A DEPTH CHART ===")
print("  %d of %d rows landed on a team" % (hit, len(O)))
print("  %d of %d matched a player id (red highlight will show)"
      % (int((O["id"] != "").sum()), len(O)))
miss = O[O["id"] == ""]["name"].tolist()
if miss:
    print("  unmatched: %s" % ", ".join(miss[:18]))

print("\n=== INJURIES PER TEAM ===")
for tm, x in O.groupby("team"):
    sk = x[x["pos"].isin(["QB", "RB", "WR", "TE", "K"])]
    print("  %-4s %2d total  %d skill" % (tm, len(x), len(sk)))
print("\nSaved news_overrides_v3.csv and updated ui_data.json")
