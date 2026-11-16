import json
import re
import pandas as pd

J = json.load(open("sleeper_proj_raw.json"))
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))

def sv(k):
    return float(V.get(k, 0.0))

def key(n):
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "",
               str(n).lower())
    return re.sub(r"[^a-z]", "", n)

rows = []
for d in J:
    p = d.get("player") or {}
    if p.get("position") != "QB":
        continue
    s = d.get("stats") or {}
    def g(k):
        v = s.get(k)
        return 0.0 if v is None else float(v)
    if g("pass_att") < 150:
        continue
    nm = ((p.get("first_name") or "") + " "
          + (p.get("last_name") or "")).strip()
    rows.append({"k": key(nm), "s_att": g("pass_att"),
                 "s_pyd": g("pass_yd"), "s_ptd": g("pass_td"),
                 "s_int": g("pass_int"), "s_ryd": g("rush_yd"),
                 "s_rtd": g("rush_td"), "gp": g("gp")})
S = pd.DataFrame(rows).drop_duplicates("k")

Q = pd.read_csv("qb_all_2026.csv")
print("qb_all columns: %s" % list(Q.columns))
Q["k"] = Q["player_display_name"].apply(key)
M = Q.merge(S, on="k", how="inner")
M = M[M["dr"] == 1].copy()
for c in ["rushing_yards", "rushing_tds"]:
    M[c] = pd.to_numeric(M[c], errors="coerce").fillna(0)
print("starters matched: %d" % len(M))

def pts(att, ypa, tdr, intr, ryd, rtd):
    return (att * ypa * sv("pass_yd")
            + att * tdr * sv("pass_td")
            + att * intr * sv("pass_int")
            + ryd * sv("rush_yd")
            + rtd * sv("rush_td"))

M["our17"] = pts(M["att"], M["ypa"], M["tdr"], M["intr"],
                 M["rushing_yards"], M["rushing_tds"]) * 17.0
M["slp_raw"] = (M["s_pyd"] * sv("pass_yd")
                + M["s_ptd"] * sv("pass_td")
                + M["s_int"] * sv("pass_int")
                + M["s_ryd"] * sv("rush_yd")
                + M["s_rtd"] * sv("rush_td"))
M["slp17"] = M["slp_raw"] * 17.0 / M["gp"].clip(lower=1)

M["sw_att"] = pts(M["s_att"] / 17.0, M["ypa"], M["tdr"],
                  M["intr"], M["rushing_yards"],
                  M["rushing_tds"]) * 17.0
M["sw_rtd"] = pts(M["att"], M["ypa"], M["tdr"], M["intr"],
                  M["rushing_yards"],
                  M["s_rtd"] / 17.0) * 17.0
M["sw_all"] = pts(M["s_att"] / 17.0, M["ypa"], M["tdr"],
                  M["intr"], M["s_ryd"] / 17.0,
                  M["s_rtd"] / 17.0) * 17.0

def gp(c, b):
    return 100.0 * (M[c] / M[b] - 1).mean()

print("\n=== DECOMPOSITION vs SLEEPER @17g ===")
print("  as built                  %+6.1f%%"
      % gp("our17", "slp17"))
print("  swap in their attempts    %+6.1f%%"
      % gp("sw_att", "slp17"))
print("  swap in their rush TDs    %+6.1f%%"
      % gp("sw_rtd", "slp17"))
print("  swap all rushing + att    %+6.1f%%"
      % gp("sw_all", "slp17"))
print("\n  vs sleeper UNNORMALIZED   %+6.1f%%"
      % gp("our17", "slp_raw"))

print("\n=== VOLUME AND RUSH TD, TOP 14 ===")
print("  %-20s %5s %5s %6s %6s"
      % ("player", "ourA", "slpA", "ourRT", "slpRT"))
for _, r in M.nlargest(14, "our17").iterrows():
    print("  %-20s %5.0f %5.0f %6.1f %6.1f"
          % (str(r["player_display_name"])[:20],
             r["att"] * 17, r["s_att"],
             r["rushing_tds"] * 17, r["s_rtd"]))
