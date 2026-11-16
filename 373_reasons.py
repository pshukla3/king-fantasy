import json, re, os
import pandas as pd
import fpts

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

WANT = {"receivingTargets": "tgt", "receptions": "rec",
        "receivingYards": "recyd",
        "rushingAttempts": "car", "rushingYards": "rushyd",
        "passingYards": "payd", "passingTouchdowns": "patd",
        "interceptions": "int"}
CATS = ("passing", "rushing", "receiving")

STAT = {}
for e in fpts.week_events(1):
    if e["state"] != "post":
        continue
    s = fpts.get(fpts.BASE + "summary?event=" + e["id"])
    for t in ((s.get("boxscore") or {}).get("players") or []):
        for c in (t.get("statistics") or []):
            if (c.get("name") or "").lower() not in CATS:
                continue
            ks = c.get("keys") or []
            for a in (c.get("athletes") or []):
                nm = (a.get("athlete") or {}).get("displayName")
                if not nm:
                    continue
                d = STAT.setdefault(norm(nm), {})
                for k, v in zip(ks, a.get("stats") or []):
                    if k in WANT:
                        d[WANT[k]] = v
print("week 1 stat lines: %d" % len(STAT))

SNAP = {}
sp = "data_usage/snaps_2026.parquet"
if os.path.exists(sp):
    S = pd.read_parquet(sp)
    for _, r in S[S["week"] == 1].iterrows():
        try:
            SNAP[norm(r["player"])] = float(r["offense_pct"])
        except (TypeError, ValueError):
            pass
print("week 1 snap shares: %d" % len(SNAP))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
W1 = {norm(r["n"]): r
      for r in json.load(open("site/_wk1.json"))["rows"]}

def num(v):
    try:
        return float(str(v).split("/")[0])
    except (ValueError, TypeError):
        return 0.0

OUT = {}
for _, r in B.iterrows():
    base, live = r.get("points"), r.get("proj_live")
    if pd.isna(base) or pd.isna(live):
        continue
    mv = float(live) - float(base)
    k, pos = r["k"], str(r["position"])
    w1, st, sn = W1.get(k), STAT.get(k, {}), SNAP.get(k)
    bits, why = [], []
    if w1:
        bits.append("%.1f pts vs %.1f projected"
                    % (w1["act"], w1["proj"]))
    if pos in ("WR", "TE") and st:
        bits.append("%s tgt, %s rec, %s yds"
                    % (st.get("tgt", "0"), st.get("rec", "0"),
                       st.get("recyd", "0")))
        if num(st.get("tgt")) <= 3:
            why.append("low target volume")
    if pos == "RB" and st:
        bits.append("%s car, %s yds" % (st.get("car", "0"),
                                        st.get("rushyd", "0")))
        if num(st.get("car")) <= 8:
            why.append("limited carries")
    if pos == "QB" and st:
        bits.append("%s yds, %s TD, %s INT"
                    % (st.get("payd", "0"),
                       st.get("patd", "0"), st.get("int", "0")))
        if num(st.get("int")) >= 2:
            why.append("multiple interceptions")
    if sn is not None:
        bits.append("%.0f%% snaps" % (100 * sn))
        if sn < 0.5:
            why.append("under half the snaps")
    inj = str(r.get("inj_status") or "")
    bad = inj.lower() in ("out", "doubtful",
                          "injured reserve", "suspension")
    if bad and w1 and w1["act"] < 0.5 * max(w1["proj"], 1):
        why.append("left injured, listed %s after - hurt "
                   "players lose 2.4 ppg off baseline vs "
                   "0.9 for a healthy bad game" % inj)
    elif inj and inj.lower() not in ("active", "nan", ""):
        why.append("listed %s" % inj)
    yrs = int(r.get("yrs") or 0)
    lam = float(r.get("lam") or 0.334)
    OUT[k] = {"n": r["player_display_name"],
              "move": round(mv, 2), "yrs": yrs,
              "weight": lam, "snap": sn, "stats": st,
              "bits": bits, "why": why,
              "line": ("%s. Projection %s %.2f (week 1 at "
                       "%.0f%% weight, %d seasons of "
                       "history).%s"
                       % ("; ".join(bits) if bits
                          else "No week 1 game",
                          "up" if mv >= 0 else "down",
                          abs(mv), 100 * lam, yrs,
                          (" Drivers: " + ", ".join(why)
                           + ".") if why else ""))}
json.dump(OUT, open("site/_reasons.json", "w"))
print("wrote site/_reasons.json (%d players)" % len(OUT))
for nm in ("Ja'Marr Chase", "Kyler Murray", "Jalen Coker",
           "Derrick Henry"):
    d = OUT.get(norm(nm))
    if d:
        print("\n%s (%+.2f)\n  %s" % (nm, d["move"],
                                      d["line"]))
