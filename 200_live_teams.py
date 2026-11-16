import json
import re
import pandas as pd

SUF = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")

def key(n):
    s = str(n).lower().replace(".", " ")
    s = SUF.sub(" ", s)
    return re.sub(r"[^a-z]", "", s)

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")

def rec(r):
    p = r["pp"]
    b = r["bye"] if "bye" in r else 0
    s = r["status"]
    return {"nm": str(r["player_display_name"]),
            "ps": str(r["position"]),
            "tm": str(r["team"]),
            "ppg": 0.0 if p != p else round(float(p), 2),
            "by": 0 if b != b else int(b),
            "rk": int(r["rank"]),
            "prk": int(r["pos_rank"]),
            "st": "" if s != s else str(s)}

NM = {}
for _, r in B.iterrows():
    NM.setdefault((key(r["player_display_name"]),
                   str(r["position"])), rec(r))

PJ = json.load(open("sleeper_players.json"))
OUT = {}
for sid, d in PJ.items():
    nm, ps = d.get("full_name"), d.get("position")
    if not nm or not ps:
        continue
    hit = NM.get((key(nm), ps))
    if hit:
        OUT[sid] = hit

ALIAS = {"LA": ["LAR"], "WAS": ["WSH"],
         "JAX": ["JAC"], "ARI": ["AZ"]}
for _, r in B[B["position"].isin(["DST", "DEF"])].iterrows():
    t = str(r["team"]).upper()
    if t and t != "NAN":
        OUT[t] = rec(r)
        for _a in ALIAS.get(t, []):
            OUT[_a] = rec(r)

json.dump(OUT, open("proj_by_sleeper_id.json", "w"))
print("board rows %d | sleeper ids mapped %d" % (len(B), len(OUT)))
print("sample: %s" % json.dumps(OUT.get("11560"))[:90])

css = open("site/_teams.css").read()
js = open("site/_teams.js").read()
js = js.replace("__PROJ__", json.dumps(OUT), 1)
H = ("<!doctype html><html><head><meta charset=utf-8>"
     "<meta name=viewport content='width=device-width,"
     "initial-scale=1'><title>Teams</title><style>"
     + css + "</style></head><body><div class=wrap>"
     "<h1>League rosters</h1><div class=sub>"
     "<span class=live></span>live from Sleeper &middot; "
     "refreshed <span id=ts>--</span> &middot; "
     "auto-refresh 60s</div>"
     "<div id=t class=grid>loading...</div>"
     "</div><script>" + js + "</script></body></html>")
open("site/teams.html", "w").write(H)
print("wrote site/teams.html %d KB" % (len(H) // 1024))

p = "112_ui_v4.py"
s = open(p).read()
a = '<button data-t="rosters">Rosters</button>'
if 'src="teams.html"' in s:
    print("teams tab already wired")
elif a in s:
    s = s.replace(a, a + '<button data-t="teams">'
                  'My League</button>', 1)
    s = s.replace('<section id="rosters"></section>',
                  '<section id="rosters"></section>\n'
                  '<section id="teams"><iframe '
                  'src="teams.html" style="width:100%;'
                  'height:2600px;border:0"></iframe>'
                  '</section>', 1)
    open(p, "w").write(s)
    print("added My League tab -> teams.html")
else:
    print("nav anchor missing - page built, not wired")
