import glob, json, re
import numpy as np
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

I = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_inj/inj_*.parquet"))],
              ignore_index=True)
NM = next(c for c in ("full_name", "player_name",
                      "player_display_name")
          if c in I.columns)
I["k"] = I[NM].map(norm)
I["season"] = I["season"].astype(int)
I["week"] = I["week"].astype(int)
I["st"] = I["report_status"].astype(str).str.lower()
OUT = {"out", "injured reserve", "doubtful"}
I["bad"] = I["st"].isin(OUT)

print("=== HOW LONG DOES EACH STATUS LAST? ===")
print("(consecutive weeks still listed out, from the "
      "first week a player is flagged)")
res = {}
for lab, keys in (("Injured Reserve", {"injured reserve"}),
                  ("Out", {"out"}),
                  ("Doubtful", {"doubtful"})):
    runs = []
    d = I[I["st"].isin(keys)]
    for (s, k), g in d.groupby(["season", "k"]):
        wk = sorted(g["week"].unique())
        if not wk:
            continue
        start = wk[0]
        allbad = set(I[(I["season"] == s) & (I["k"] == k)
                       & I["bad"]]["week"])
        n, w = 0, start
        while w in allbad and n < 18:
            n += 1
            w += 1
        runs.append(n)
    if len(runs) > 40:
        res[lab] = float(np.median(runs))
        print("  %-16s n=%-5d median %.1f weeks | "
              "mean %.1f | 75th %.1f"
              % (lab, len(runs), np.median(runs),
                 np.mean(runs), np.percentile(runs, 75)))
json.dump(res, open("inj_weeks.json", "w"), indent=1)

WK = 2
LEFT = 18 - WK
MISS = {"injured reserve": res.get("Injured Reserve", 4.0),
        "out": res.get("Out", 1.5),
        "doubtful": res.get("Doubtful", 1.2),
        "suspension": 3.0,
        "physically unable to perform": 6.0,
        "questionable": 0.4}

INJ = json.load(open("site/_inj.json"))
B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)

def avail(k):
    j = INJ.get(k)
    if not j:
        return 1.0, ""
    st = str(j.get("status") or "").lower()
    m = MISS.get(st)
    if m is None:
        return 1.0, j.get("status", "")
    return max(0.05, (LEFT - m) / LEFT), j.get("status", "")

av = B["k"].map(lambda k: avail(k)[0])
B["avail"] = av.round(3)
B["inj_now"] = B["k"].map(lambda k: avail(k)[1])
col = "mvorp" if "mvorp" in B.columns else "vorp"
B[col] = pd.to_numeric(B[col], errors="coerce")

# rank penalty proportional to games expected to be missed
B["rk_pen"] = ((1.0 - B["avail"]) * 0.9
               * B["rank_v"].clip(upper=250)).round(1)
B["adj2"] = B["rank_v"] + B["rk_pen"]
B = B.sort_values("adj2")
B["rank_v"] = range(1, len(B) + 1)
B["upd_rank"] = B["rank_v"]
B.drop(columns=["k"]).to_csv("board_final.csv",
                             index=False)

print("\n=== PLAYERS PUSHED DOWN BY INJURY ===")
z = B[B["rk_pen"] > 0].sort_values("rk_pen",
                                   ascending=False)
print("%-24s %-16s %6s %6s"
      % ("PLAYER", "STATUS", "AVAIL", "DROP"))
for _, r in z.head(14).iterrows():
    print("%-24s %-16s %5.0f%% %6.0f"
          % (r["player_display_name"][:24],
             str(r["inj_now"])[:16], 100 * r["avail"],
             r["rk_pen"]))
print("\n%d players carry an injury penalty" % len(z))
