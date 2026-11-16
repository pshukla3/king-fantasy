import json, re, os
import pandas as pd
import fpts

W_PTS, W_TCH, W_SNP = 0.0897, 0.1214, 3.1564

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

WANT = {"receivingTargets": "tgt",
        "rushingAttempts": "car"}
STAT = {}
for e in fpts.week_events(1):
    if e["state"] != "post":
        continue
    s = fpts.get(fpts.BASE + "summary?event=" + e["id"])
    for t in ((s.get("boxscore") or {}).get("players") or []):
        for c in (t.get("statistics") or []):
            if (c.get("name") or "").lower() not in \
                    ("rushing", "receiving"):
                continue
            ks = c.get("keys") or []
            for a in (c.get("athletes") or []):
                nm = (a.get("athlete") or {}).get("displayName")
                if not nm:
                    continue
                d = STAT.setdefault(norm(nm), {})
                for k, v in zip(ks, a.get("stats") or []):
                    if k in WANT:
                        try:
                            d[WANT[k]] = float(v)
                        except (TypeError, ValueError):
                            pass
print("week 1 usage lines: %d" % len(STAT))

H = pd.read_parquet("weekly_all.parquet")
H = H[H["season"] == 2025].copy()
H["k"] = H["player_display_name"].map(norm)
for c in ("targets", "carries"):
    H[c] = pd.to_numeric(H.get(c), errors="coerce")\
        .fillna(0.0)
H["touch"] = H["targets"] + H["carries"]
TYPT = H.groupby("k")["touch"].mean().to_dict()

S26 = {}
TYPS = {}
if os.path.exists("data_usage/snaps_2026.parquet"):
    d = pd.read_parquet("data_usage/snaps_2026.parquet")
    for _, r in d[d["week"] == 1].iterrows():
        try:
            S26[norm(r["player"])] = float(r["offense_pct"])
        except (TypeError, ValueError):
            pass
if os.path.exists("data_usage/snaps_2025.parquet"):
    d = pd.read_parquet("data_usage/snaps_2025.parquet")
    d["k"] = d["player"].map(norm)
    TYPS = d.groupby("k")["offense_pct"].median().to_dict()

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
W1 = {norm(r["n"]): r
      for r in json.load(open("site/_wk1.json"))["rows"]}

out, expl = [], {}
for _, r in B.iterrows():
    base = r.get("points")
    if pd.isna(base):
        out.append(None)
        continue
    k = r["k"]
    w1 = W1.get(k)
    if not w1:
        out.append(round(float(base), 2))
        continue
    base = float(base)
    st = STAT.get(k, {})
    touch = st.get("tgt", 0.0) + st.get("car", 0.0)
    typt = TYPT.get(k)
    snap = S26.get(k)
    typs = TYPS.get(k)
    part = 1.0 if (snap is None or not typs or typs < .05) \
        else max(0.0, min(1.0, snap / typs))
    dp = (float(w1["act"]) - base) * W_PTS * part
    dt = ((touch - typt) * W_TCH * part
          if typt is not None else 0.0)
    ds = ((snap - typs) * W_SNP
          if (snap is not None and typs) else 0.0)
    val = round(base + dp + dt + ds, 2)
    out.append(val)
    expl[k] = {"base": round(base, 2), "live": val,
               "d_pts": round(dp, 2),
               "d_touch": round(dt, 2),
               "d_snap": round(ds, 2),
               "touch": touch, "typt": typt,
               "snap": snap, "typs": typs}
B["proj_live"] = out
B = B.drop(columns=["k"])
B.to_csv("board_final.csv", index=False)
json.dump(expl, open("site/_decomp.json", "w"))
print("wrote site/_decomp.json (%d players)" % len(expl))

print("\n%-22s %6s %7s %7s %7s %7s"
      % ("PLAYER", "BASE", "dPTS", "dTOUCH", "dSNAP", "NEW"))
for nm in ("Ja'Marr Chase", "Kyler Murray",
           "Derrick Henry", "Jalen Coker",
           "Ashton Jeanty", "Jordan Addison"):
    d = expl.get(norm(nm))
    if d:
        print("%-22s %6.2f %+7.2f %+7.2f %+7.2f %7.2f"
              % (nm[:22], d["base"], d["d_pts"],
                 d["d_touch"], d["d_snap"], d["live"]))
