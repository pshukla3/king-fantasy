import json, re, statistics as st
import nflreadpy as nfl

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

def g(r, k):
    v = r.get(k, 0)
    try:
        return float(v) if v == v else 0.0
    except Exception:
        return 0.0

def passpts(r):
    return (g(r, "passing_yards") * 0.04
            + g(r, "passing_tds") * 4
            + g(r, "passing_interceptions") * -1
            + g(r, "passing_2pt_conversions") * 2)

def rushpts(r):
    return (g(r, "rushing_yards") * 0.1
            + g(r, "rushing_tds") * 6
            + g(r, "rushing_2pt_conversions") * 2
            + g(r, "rushing_fumbles_lost") * -2)

def recpts(r):
    return (g(r, "receptions") * 1.0
            + g(r, "receiving_yards") * 0.1
            + g(r, "receiving_tds") * 6
            + g(r, "receiving_2pt_conversions") * 2
            + g(r, "receiving_fumbles_lost") * -2)

B = json.load(open("site/_board.json"))
PROJ = {norm(r["n"]): r for r in B["rows"]}

print("loading stats")
d = nfl.load_player_stats([2026]).to_pandas()
d = d[d["week"] <= 3].copy()
d["pp"] = d.apply(passpts, axis=1)
d["rp"] = d.apply(rushpts, axis=1)
d["cp"] = d.apply(recpts, axis=1)
d["fp"] = d["pp"] + d["rp"] + d["cp"]

ag = d.groupby(["player_display_name", "position"],
               as_index=False).agg(
    fp=("fp", "mean"), pp=("pp", "mean"),
    rp=("rp", "mean"), n=("fp", "size"))
ag = ag[ag["n"] >= 2]

print("\n=== SPREAD: proj SD vs real SD ===")
print("%-5s %6s %9s %9s %7s" % ("POS", "N", "REAL", "PROJ", "RATIO"))
for pos in ("QB", "RB", "WR", "TE"):
    s = ag[ag["position"] == pos]
    R, P = [], []
    for _, r in s.iterrows():
        p = PROJ.get(norm(r["player_display_name"]))
        if p and p.get("live"):
            R.append(r["fp"]); P.append(p["live"])
    if len(R) < 8:
        continue
    rs, ps = st.pstdev(R), st.pstdev(P)
    print("%-5s %6d %9.2f %9.2f %7.2f%s"
          % (pos, len(R), rs, ps, ps / rs,
             "  OVER-SHRUNK" if ps / rs < .65 else ""))

print("\n=== QB: pass vs rush split (why Allen != Brissett) ===")
q = ag[(ag["position"] == "QB") & (ag["fp"] > 8)]
q = q.sort_values("fp", ascending=False).head(16)
print("  %-22s %7s %7s %7s %7s %7s"
      % ("QB", "ACTUAL", "PASS", "RUSH", "RUSH%", "PROJ"))
for _, r in q.iterrows():
    p = PROJ.get(norm(r["player_display_name"]))
    pv = p["live"] if p else 0
    sh = r["rp"] / r["fp"] * 100 if r["fp"] else 0
    print("  %-22s %7.1f %7.1f %7.1f %6.0f%% %7.1f"
          % (r["player_display_name"][:22], r["fp"],
             r["pp"], r["rp"], sh, pv))

print("\n=== stability: rush vs pass points, wk-to-wk ===")
h = nfl.load_player_stats([2024, 2025]).to_pandas()
h["pp"] = h.apply(passpts, axis=1)
h["rp"] = h.apply(rushpts, axis=1)
h = h[(h["position"] == "QB") & (h["attempts"] >= 15)]
for lbl, col in (("passing pts", "pp"), ("rushing pts", "rp")):
    xs, ys = [], []
    for (pid,), grp in h.groupby(["player_id"]):
        v = grp.sort_values(["season", "week"])[col].tolist()
        for i in range(len(v) - 1):
            xs.append(v[i]); ys.append(v[i + 1])
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = sum((a - mx) ** 2 for a in xs) ** .5
    vy = sum((b - my) ** 2 for b in ys) ** .5
    print("  %-14s r = %.3f   (n=%d)" % (lbl, cov / (vx * vy), n))
