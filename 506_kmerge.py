import json, re
import numpy as np

BANDS = ["0_19", "20_29", "30_39", "40_49", "50_59", "60_"]
DEF = {"fgm_0_19": 3, "fgm_20_29": 3, "fgm_30_39": 3,
       "fgm_40_49": 4, "fgm_50p": 5, "fgmiss": -1,
       "xpm": 1, "xpmiss": 0}
try:
    MINE = json.load(open("league_scoring.json"))
except Exception:
    MINE = DEF

from namekey import nk as norm

def score(r, S):
    if r.get("out") or r.get("o") == "BYE":
        return 0.0
    t = 0.0
    for b in BANDS:
        key = ("fgm_50p" if b in ("50_59", "60_")
               else "fgm_" + b)
        pts = S.get(key)
        if pts is None:
            pts = S.get("fgm_" + b, 3)
        t += r["m_" + b] * pts
        t += (r["a_" + b] - r["m_" + b]) * S.get("fgmiss", -1)
    t += r["xm"] * S.get("xpm", 1)
    t += (r["xa"] - r["xm"]) * S.get("xpmiss", 0)
    return round(t, 2)


# Sleeper and nflverse disagree on a few team codes.
TEAMFIX = {"LAR": "LA", "OAK": "LV", "SD": "LAC",
           "SL": "LA", "STL": "LA", "ARZ": "ARI",
           "BLT": "BAL", "CLV": "CLE", "HST": "HOU",
           "WSH": "WAS", "JAC": "JAX"}
def tfix(t):
    t = (t or "").upper()
    return TEAMFIX.get(t, t)

BACKUP_ODDS = 0.12   # rough chance a backup ends up kicking
bench = []

K = json.load(open("site/_kproj.json"))
B = json.load(open("site/_board.json"))
IDX = {}
for k, v in K.items():
    IDX[k] = v
    for sf in (" jr", " ii", " iii", " iv", " v"):
        if k.endswith(sf):
            IDX.setdefault(k[:-len(sf)], v)

hit = 0
starters = set()
for r in B["rows"]:
    if r.get("pos") != "K":
        continue
    v = IDX.get(norm(r.get("n")))
    if not v:
        # A backup kicker is not worthless -- he is a call
        # option on the starter getting hurt. Price him at
        # that probability times his team's starter output.
        r["kbench"] = 1
        r["wk"] = []
        r["conf"] = "low"
        r["conf_why"] = ("not the starter -- valued only on "
                         "the chance he takes the job")
        bench.append(r)
        continue
    wk = []
    for x in v["wk"]:
        row = dict(x)
        row["m"] = score(x, DEF)
        row["ml"] = score(x, MINE)
        wk.append(row)
    play = [x for x in wk
            if x["o"] != "BYE" and not x.get("out")]
    r["wk"] = wk
    r["live"] = round(float(np.mean(
        [x["m"] for x in play])), 2) if play else 0.0
    r["live_lg"] = round(float(np.mean(
        [x["ml"] for x in play])), 2) if play else 0.0
    r["base"] = r["live"]
    r["sim"] = 20000
    r["leg"] = v.get("leg")
    # kicker week-to-week autocorrelation is r=0.04
    r["conf"] = "low"
    r["conf_why"] = ("kicker scoring is near-random "
                     "week to week (r=0.04 over 10 yrs)")
    # fill the display fields the rankings page renders.
    # floor/ceil come straight from the 20k sims; games
    # from the schedule; nothing here is invented.
    if play:
        r["floor"] = round(float(np.mean(
            [x["lo"] for x in play if "lo" in x] or [0])), 1)
        r["ceil"] = round(float(np.mean(
            [x["hi"] for x in play if "hi" in x] or [0])), 1)
    # the rankings table (379_boardui) reads these four.
    # all derived from the 20k sims -- nothing invented.
    if play:
        r["s_cons"] = int(round(sum(x["m"] for x in play)))
        r["s_floor"] = int(round(sum(x.get("lo", 0)
                                     for x in play)))
        r["s_ceil"] = int(round(sum(x.get("hi", 0)
                                    for x in play)))
        _m = [x["m"] for x in play]
        _mu = sum(_m) / len(_m)
        _sd = (sum((y - _mu) ** 2 for y in _m)
               / max(1, len(_m) - 1)) ** 0.5
        r["risk"] = round(_sd / _mu, 3) if _mu else 0.0
    a = r.get("adp")
    if a:
        _rd = int((a - 1) // 10) + 1
        _pk = int(a - (_rd - 1) * 10)
        r["adp_rp"] = "%d.%02d" % (_rd, _pk)
    r["s_ds"] = r.get("s_cons")
    r["s_upd"] = r.get("s_cons")
    r["games"] = float(len(play))
    r["gm"] = 17
    r["logo"] = (r.get("tm") or "").lower()
    r.setdefault("inj", "Active")
    r.setdefault("risk", 0.0)
    r.setdefault("sos", 0.0)
    r.setdefault("sos_pct", 0.0)
    starters.add(norm(r["n"]))
    hit += 1
ks = [r for r in B["rows"] if r.get("pos") == "K"
      and r.get("live")]
ks.sort(key=lambda r: -r["live"])
# tier + a fallback trade value so no kicker renders blank
for i, r in enumerate(ks, 1):
    r["tier"] = 10 + (i - 1) // 4
    # overwrite ALL kicker values on one scale -- the 11
    # legacy rows carried a different system, so the top
    # kicker was showing less value than the 4th.
    r["val"] = max(1, int(round(12 - (i - 1) * 0.30)))
    r["uval"] = r["val"]
    r.setdefault("urk", r.get("rk"))

# now price the backups off their own team's starter
STARTER = {}
for r in B["rows"]:
    if r.get("pos") == "K" and r.get("live") and not r.get("kbench"):
        STARTER[tfix(r.get("tm"))] = r
for r in bench:
    st = STARTER.get(tfix(r.get("tm")))
    if not st:
        r["live"] = r["base"] = r["vorp"] = 0.0
        continue
    f = BACKUP_ODDS
    r["live"] = round((st.get("live") or 0) * f, 2)
    r["live_lg"] = round((st.get("live_lg") or 0) * f, 2)
    r["base"] = r["live"]
    r["floor"] = 0.0
    r["ceil"] = st.get("ceil")
    r["games"] = 0.0
    r["gm"] = 17
    r["logo"] = (r.get("tm") or "").lower()
    r.setdefault("inj", "Active")
    r["risk"] = 0.95
    r["sos_pct"] = 0.0
    for k2 in ("s_cons", "s_floor", "s_ceil"):
        if st.get(k2) is not None:
            r[k2] = int(round(st[k2] * f))
    r["s_ds"] = r.get("s_cons")
    r["s_upd"] = r.get("s_cons")
    a_ = r.get("adp")
    if a_:
        _rd = int((a_ - 1) // 10) + 1
        r["adp_rp"] = "%d.%02d" % (_rd, int(a_ - (_rd - 1) * 10))
    r["tier"] = 20
    r["val"] = 1
    r["uval"] = 1
print("priced %d backup kickers at %.0f%% of their starter"
      % (len(bench), BACKUP_ODDS * 100))

json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))

print("\n%-3s %-24s %-4s %8s %8s %7s"
      % ("#", "KICKER", "TM", "DEFAULT", "YOURS", "50+%"))
for i, r in enumerate(ks, 1):
    print("%-3d %-24s %-4s %8.2f %8.2f %6.1f%%"
          % (i, r["n"][:24], r.get("tm"), r["live"],
             r.get("live_lg") or 0, (r.get("leg") or 0) * 100))
