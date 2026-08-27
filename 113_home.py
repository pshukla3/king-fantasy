import json
import re
import pandas as pd
import nflreadpy as nfl

SEASON = 2026

DIV = {
 "BUF": "AFC East", "MIA": "AFC East", "NE": "AFC East",
 "NYJ": "AFC East",
 "BAL": "AFC North", "CIN": "AFC North", "CLE": "AFC North",
 "PIT": "AFC North",
 "HOU": "AFC South", "IND": "AFC South", "JAX": "AFC South",
 "TEN": "AFC South",
 "DEN": "AFC West", "KC": "AFC West", "LAC": "AFC West",
 "LV": "AFC West",
 "DAL": "NFC East", "NYG": "NFC East", "PHI": "NFC East",
 "WAS": "NFC East",
 "CHI": "NFC North", "DET": "NFC North", "GB": "NFC North",
 "MIN": "NFC North",
 "ATL": "NFC South", "CAR": "NFC South", "NO": "NFC South",
 "TB": "NFC South",
 "ARI": "NFC West", "LA": "NFC West", "SEA": "NFC West",
 "SF": "NFC West"}

LOGO = {
 "ARI": "ari", "AZ": "ari", "ATL": "atl", "BAL": "bal",
 "BUF": "buf", "CAR": "car", "CHI": "chi", "CIN": "cin",
 "CLE": "cle", "DAL": "dal", "DEN": "den", "DET": "det",
 "GB": "gb", "HOU": "hou", "IND": "ind", "JAX": "jax",
 "KC": "kc", "LV": "lv", "LAC": "lac", "LA": "lar",
 "LAR": "lar", "MIA": "mia", "MIN": "min", "NE": "ne",
 "NO": "no", "NYG": "nyg", "NYJ": "nyj", "PHI": "phi",
 "PIT": "pit", "SF": "sf", "SEA": "sea", "TB": "tb",
 "TEN": "ten", "WAS": "wsh", "WSH": "wsh"}

def logo(t):
    k = LOGO.get(str(t).strip().upper())
    if not k:
        return ""
    return "https://a.espncdn.com/i/teamlogos/nfl/500/%s.png" % k

def esc(s):
    s = str(s if s is not None else "")
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return s.replace(">", "&gt;").replace('"', "&quot;")

def num(v, d=1):
    try:
        f = float(v)
    except Exception:
        return None
    if f != f:
        return None
    return round(f, d)

S = nfl.load_schedules(seasons=[SEASON])
S = S.to_pandas() if hasattr(S, "to_pandas") else S
if "game_type" in S.columns:
    REG = S[S["game_type"] == "REG"].copy()
else:
    REG = S.copy()
REG["gd"] = pd.to_datetime(REG["gameday"], errors="coerce")
done = REG[REG["home_score"].notna()].copy()
print("2026 regular season games: %d" % len(REG))
print("completed so far: %d" % len(done))

GAMES = []
for _, r in done.sort_values("gd").tail(6).iterrows():
    d = r["gd"]
    GAMES.append({
        "wk": int(r["week"]),
        "day": "" if d != d else d.strftime("%a %b %d"),
        "time": "FINAL",
        "away": str(r["away_team"]),
        "home": str(r["home_team"]),
        "spread": None, "total": None,
        "asc": int(r["away_score"]),
        "hsc": int(r["home_score"])})

up = REG[REG["home_score"].isna()].sort_values(["gd", "week"])
for _, r in up.head(18).iterrows():
    d = r["gd"]
    GAMES.append({
        "wk": int(r["week"]),
        "day": "" if d != d else d.strftime("%a %b %d"),
        "time": str(r.get("gametime") or ""),
        "away": str(r["away_team"]),
        "home": str(r["home_team"]),
        "spread": num(r.get("spread_line")),
        "total": num(r.get("total_line")),
        "asc": None, "hsc": None})
print("scoreboard cards: %d" % len(GAMES))

ST = {}
for t in DIV:
    ST[t] = {"tm": t, "div": DIV[t], "w": 0, "l": 0, "t": 0,
             "pf": 0.0, "pa": 0.0}
for _, r in done.iterrows():
    h = str(r["home_team"])
    a = str(r["away_team"])
    hs = float(r["home_score"])
    ac = float(r["away_score"])
    for tm, own, opp in ((h, hs, ac), (a, ac, hs)):
        if tm not in ST:
            continue
        ST[tm]["pf"] += own
        ST[tm]["pa"] += opp
        if own > opp:
            ST[tm]["w"] += 1
        elif own < opp:
            ST[tm]["l"] += 1
        else:
            ST[tm]["t"] += 1

REC = {}
for t, v in ST.items():
    if v["t"]:
        REC[t] = "%d-%d-%d" % (v["w"], v["l"], v["t"])
    else:
        REC[t] = "%d-%d" % (v["w"], v["l"])

ORDER = ["AFC East", "AFC North", "AFC South", "AFC West",
         "NFC East", "NFC North", "NFC South", "NFC West"]
STAND = sorted(ST.values(),
               key=lambda x: (ORDER.index(x["div"]), -x["w"],
                              x["l"], -x["pf"]))
print("standings teams: %d" % len(STAND))

BOX = []
if len(done):
    try:
        P = nfl.load_pbp(seasons=[SEASON])
        P = P.to_pandas() if hasattr(P, "to_pandas") else P

        def col(c):
            if c in P.columns:
                return pd.to_numeric(P[c],
                                     errors="coerce").fillna(0)
            return pd.Series(0.0, index=P.index)

        P = P[P["posteam"].notna()].copy()
        P["_s"] = (col("rush_attempt") + col("pass_attempt")) > 0
        P["_y"] = col("yards_gained") * P["_s"]
        P["_p"] = col("passing_yards")
        P["_r"] = col("rushing_yards")
        P["_t"] = col("interception") + col("fumble_lost")
        P["_f"] = col("first_down")
        G = P.groupby(["game_id", "posteam"]).agg(
            plays=("_s", "sum"), yds=("_y", "sum"),
            pas=("_p", "sum"), rus=("_r", "sum"),
            to=("_t", "sum"), fd=("_f", "sum")).reset_index()
        for _, r in G.sort_values("game_id").tail(20).iterrows():
            BOX.append({"tm": str(r["posteam"]),
                        "plays": int(r["plays"]),
                        "yds": int(r["yds"]), "pas": int(r["pas"]),
                        "rus": int(r["rus"]), "fd": int(r["fd"]),
                        "to": int(r["to"])})
        print("box lines: %d team-games" % len(BOX))
    except Exception as e:
        print("pbp not available yet: %s" % e)
else:
    print("no completed games - box lines fill after Week 1")

def strip(s):
    return re.sub(r"<[^>]+>", "", str(s or "")).strip()

try:
    N = json.load(open("news_2026.json"))
    arts = N.get("articles", [])
except Exception as e:
    print("news_2026.json missing: %s" % e)
    arts = []

hero = None
for a in arts:
    if a.get("img"):
        hero = a
        break
NEWS = [a for a in arts if not (hero and a is hero)][:9]
BUILT = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%MZ")
print("hero: %s" % (hero["hd"][:52] if hero else "NONE"))
print("news items: %d" % len(NEWS))

CSS = """
<style>
.scorebar{background:#0e1117;border-bottom:1px solid var(--line);
 position:sticky;top:0;z-index:60}
.sbin{display:flex;overflow-x:auto;scrollbar-width:thin}
.sbin::-webkit-scrollbar{height:5px}
.sbin::-webkit-scrollbar-thumb{background:#2b3240}
.sbc{flex:0 0 176px;padding:8px 12px;
 border-right:1px solid var(--line)}
.sbrow{display:flex;align-items:center;gap:8px;
 font-size:13px;font-weight:700;color:var(--text);margin:2px 0}
.sbrow img{width:22px;height:22px;object-fit:contain}
.sbrow span.ab{flex:1;letter-spacing:.02em}
.sbrow span.vv{color:var(--dim);font-weight:600;font-size:12px}
.sbrow span.win{color:var(--sky)}
.sbmeta{margin-top:6px;font-size:10px;letter-spacing:.07em;
 color:var(--dim);text-transform:uppercase}
.welc{background:linear-gradient(100deg,#123',#0b0d10);
 border:1px solid var(--line);border-radius:12px;
 padding:24px 26px;margin:4px 0 20px}
.welc h1{margin:0 0 6px;font-size:27px;color:#fff;
 letter-spacing:-.01em}
.welc h1 em{font-style:normal;color:var(--sky)}
.welc p{margin:0;color:var(--dim);font-size:14px;max-width:640px;
 line-height:1.55}
.hero{position:relative;border-radius:12px;overflow:hidden;
 margin-bottom:20px;border:1px solid var(--line)}
.hero img{width:100%;height:340px;object-fit:cover;display:block}
.hgrad{position:absolute;inset:0;background:linear-gradient(
 to top,rgba(6,8,11,.97) 10%,rgba(6,8,11,.5) 50%,
 rgba(6,8,11,0) 82%)}
.htx{position:absolute;left:0;right:0;bottom:0;padding:22px 24px}
.htag{display:inline-block;background:var(--sky);color:#06090d;
 font-size:10px;font-weight:800;letter-spacing:.09em;
 padding:3px 8px;border-radius:3px;text-transform:uppercase}
.htx h2{margin:10px 0 6px;font-size:29px;line-height:1.18;
 color:#fff;max-width:740px}
.htx p{margin:0;color:#b7c0cc;font-size:14px;max-width:660px}
.hgrid{display:grid;grid-template-columns:1.55fr 1fr;gap:22px}
@media(max-width:900px){.hgrid{grid-template-columns:1fr}
 .hero img{height:210px}.htx h2{font-size:20px}}
.hsec{font-size:12px;letter-spacing:.1em;color:var(--sky);
 text-transform:uppercase;font-weight:800;margin:0 0 10px;
 padding-bottom:8px;border-bottom:2px solid var(--line)}
.nrow{display:flex;gap:11px;padding:10px 0;
 border-bottom:1px solid var(--line)}
.nrow img{width:88px;height:58px;object-fit:cover;
 border-radius:6px;flex:0 0 88px;background:#1c2028}
.nrow a{color:var(--text);text-decoration:none;font-weight:600;
 font-size:13.5px;line-height:1.35;display:block}
.nrow a:hover{color:var(--sky)}
.nmeta{font-size:11px;color:var(--dim);margin-top:5px}
.brk{color:#ff8b6b;font-weight:800}
.dvh{font-size:10.5px;letter-spacing:.09em;color:var(--sky);
 text-transform:uppercase;font-weight:800;padding-top:14px}
table.st{width:100%;border-collapse:collapse;font-size:13px}
table.st td,table.st th{padding:5px 4px;text-align:right;
 border-bottom:1px solid var(--line)}
table.st th{color:var(--dim);font-size:10px;font-weight:700;
 letter-spacing:.05em;text-transform:uppercase}
table.st td.tm,table.st th.tm{text-align:left}
table.st td.tm img{width:22px;height:22px;object-fit:contain;
 vertical-align:middle;margin-right:7px}
table.st td.tm b{font-weight:600;vertical-align:middle}
.hnote{color:var(--dim);font-size:12px;line-height:1.6;
 margin-top:12px}
</style>
</head>"""
CSS = CSS.replace("#123',", "#101a26,")

def card(g):
    ar = REC.get(g["away"], "")
    hr = REC.get(g["home"], "")
    if g["asc"] is not None:
        aw = "win" if g["asc"] > g["hsc"] else ""
        hw = "win" if g["hsc"] > g["asc"] else ""
        av = '<span class="vv %s">%d</span>' % (aw, g["asc"])
        hv = '<span class="vv %s">%d</span>' % (hw, g["hsc"])
        meta = "Week %d &middot; FINAL" % g["wk"]
    else:
        av = '<span class="vv">%s</span>' % esc(ar)
        hv = '<span class="vv">%s</span>' % esc(hr)
        bits = [x for x in [g["day"], g["time"]] if x]
        meta = "Week %d &middot; %s" % (g["wk"], esc(" ".join(bits)))
    row = ('<div class="sbrow"><img src="%s" alt="%s">'
           '<span class="ab">%s</span>%s</div>')
    return ('<div class="sbc">'
            + row % (logo(g["away"]), esc(g["away"]),
                     esc(g["away"]), av)
            + row % (logo(g["home"]), esc(g["home"]),
                     esc(g["home"]), hv)
            + '<div class="sbmeta">%s</div></div>' % meta)

BAR = ('<div class="scorebar"><div class="sbin">'
       + "".join(card(g) for g in GAMES) + '</div></div>')
print("scorebar html: %d chars" % len(BAR))

W = ('<div class="welc"><h1>Welcome to <em>VaporAI</em></h1>'
     '<p>A persistence-tested fantasy football engine. Every '
     'weight in it was measured against year-over-year data, '
     'not chosen &mdash; signals that did not repeat were '
     'dropped and labelled. Live scoreboard, league news, '
     'standings and post-game box lines below; projections, '
     'rankings and your roster in the tabs above.</p></div>')

HR = ""
if hero:
    HR = ('<div class="hero"><img src="%s" alt="">'
          '<div class="hgrad"></div><div class="htx">'
          '<span class="htag">Top Story</span><h2>%s</h2>'
          '<p>%s</p></div></div>'
          % (esc(hero["img"]), esc(hero["hd"]),
             esc(strip(hero.get("dk"))[:210])))

NL = '<h3 class="hsec">Around the NFL</h3>'
for n in NEWS:
    im = ''
    if n.get("img"):
        im = '<img src="%s" alt="">' % esc(n["img"])
    tag = '<span class="brk">BREAKING</span> &middot; ' \
        if n.get("ins") else ''
    NL += ('<div class="nrow">%s<div>'
           '<a href="%s" target="_blank" rel="noopener">%s</a>'
           '<div class="nmeta">%s%s</div></div></div>'
           % (im, esc(n.get("url", "")), esc(n["hd"]), tag,
              esc(str(n.get("ts", ""))[:10])))

SD = '<h3 class="hsec">2026 Standings</h3><table class="st">'
last = ""
for s in STAND:
    if s["div"] != last:
        last = s["div"]
        SD += ('<tr><td class="tm dvh" colspan="5">%s</td></tr>'
               '<tr><th class="tm">Team</th><th>W</th><th>L</th>'
               '<th>PF</th><th>PA</th></tr>' % esc(s["div"]))
    SD += ('<tr><td class="tm"><img src="%s" alt="%s">'
           '<b>%s</b></td><td>%d</td><td>%d</td>'
           '<td>%d</td><td>%d</td></tr>'
           % (logo(s["tm"]), esc(s["tm"]), esc(s["tm"]),
              s["w"], s["l"], round(s["pf"]), round(s["pa"])))
SD += '</table>'

BX = '<h3 class="hsec" style="margin-top:26px">Team Box Lines</h3>'
if BOX:
    BX += ('<table class="st"><tr><th class="tm">Team</th>'
           '<th>Plays</th><th>Yds</th><th>Pass</th><th>Rush</th>'
           '<th>1st</th><th>TO</th></tr>')
    for b in BOX:
        BX += ('<tr><td class="tm"><img src="%s" alt="">'
               '<b>%s</b></td><td>%d</td><td>%d</td><td>%d</td>'
               '<td>%d</td><td>%d</td><td>%d</td></tr>'
               % (logo(b["tm"]), esc(b["tm"]), b["plays"],
                  b["yds"], b["pas"], b["rus"], b["fd"], b["to"]))
    BX += '</table>'
else:
    BX += ('<p class="hnote">No 2026 regular-season games have '
           'been played yet, so there is nothing to box. These '
           'fill automatically from play-by-play within a day of '
           'each game &mdash; plays, scrimmage yards, pass and '
           'rush splits, first downs and turnovers per team. '
           'nflreadpy publishes after games end, not during '
           'them, so this is post-game, not live.</p>')

HOME = ('<section class="on" id="home">' + W + HR
        + '<div class="hgrid"><div>' + BX
        + '</div><div>' + NL + '<div style="height:26px"></div>'
        + SD + '<p class="hnote">Records count completed 2026 '
        'regular-season games only, so every team reads 0-0 '
        'until Week 1 finishes. Built ' + esc(BUILT)
        + '.</p></div></div></section>')

H = open("vaporai.html").read()
A1 = '<section class="on" id="home"></section>'
A2 = "</head>"
A3 = "<body>"
A4 = "</script></body></html>"
for a in (A1, A2, A3, A4):
    assert a in H, "MISSING ANCHOR: %r" % a

H = H.replace(A2, CSS, 1)
H = H.replace(A3, A3 + BAR, 1)
H = H.replace(A1, HOME, 1)
H = H.replace(A4, "\n" + "function drawHome(){}" + "\n" + A4, 1)
open("vaporai.html", "w").write(H)

print("\n=== VERIFY ===")
V = open("vaporai.html").read()
for k, lbl in [('class="scorebar"', "top scorebar"),
               ("Welcome to <em>VaporAI</em>", "welcome banner"),
               ('class="hero"', "news hero"),
               ("Around the NFL", "news rail"),
               ("2026 Standings", "standings"),
               ("Team Box Lines", "box lines"),
               ("a.espncdn.com", "team logos")]:
    print("  %-16s %s" % ("OK" if k in V else "MISSING", lbl))
print("\nSaved vaporai.html  (%.1f MB)" % (len(V) / 1e6))
