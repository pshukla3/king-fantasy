import json
import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
B["ad"] = pd.to_numeric(B["adp"], errors="coerce")
B = B[B["pp"].fillna(0) > 0].sort_values("rank")
B = B.head(300)

C = json.load(open("player_cards.json"))
REC = {}
for k, v in C.items():
    d = v.get("p26") or {}
    r = d.get("rec")
    if r:
        REC[k] = float(r) / 17.0
print("players with 2026 rec/g: %d" % len(REC))

P = []
for _, r in B.iterrows():
    pid = str(r["player_id"])
    rg = REC.get(pid, 0.0)
    full = float(r["pp"])
    by = r["bye"] if "bye" in r else 0
    a = r["ad"]
    P.append({"n": str(r["player_display_name"]),
              "p": str(r["position"]),
              "t": str(r["team"]),
              "b": int(by) if by == by else 0,
              "g": round(full, 2),
              "gh": round(max(0.0, full - rg * 0.5), 2),
              "gs": round(max(0.0, full - rg * 1.0), 2),
              "v": round(float(r["vorp"]), 2),
              "a": round(float(a), 1) if a == a
                   else float(r["rank"]),
              "r": int(r["rank"]), "id": pid})
json.dump(P, open("site/_mock.json", "w"))
print("pool %d players" % len(P))
d = [x for x in P if x["g"] != x["gs"]][:5]
for x in d:
    print("  %-22s full %5.2f half %5.2f std %5.2f"
          % (x["n"][:22], x["g"], x["gh"], x["gs"]))

CSS = """
body{margin:0;background:#0a0a0c;color:#e6e8ec;
font:13px/1.5 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.w{max-width:1480px;margin:0 auto;padding:16px}
h1{font-size:19px;letter-spacing:-.02em;margin:0}
h2{font-size:10px;letter-spacing:.09em;font-weight:700;
text-transform:uppercase;color:#878c96;margin:16px 0 6px}
.cfg{display:flex;gap:20px;flex-wrap:wrap;
padding:14px 0;border-bottom:1px solid #24262d;
margin-bottom:14px}
.fld{display:flex;flex-direction:column;gap:4px}
.fld label{font-size:10px;letter-spacing:.09em;
text-transform:uppercase;color:#878c96;font-weight:700}
select,input,button{background:#16181d;color:#e6e8ec;
border:1px solid #24262d;border-radius:3px;
padding:6px 9px;font-size:13px;font-family:inherit}
button{cursor:pointer}
button:hover:not(:disabled){background:#24262d;
border-color:#c3c9d4}
button:disabled{opacity:.3;cursor:default}
#go{background:#c3c9d4;color:#0a0a0c;font-weight:700;
letter-spacing:.06em;text-transform:uppercase;
border-color:#c3c9d4;padding:7px 18px}
#st{color:#a8aeb9;margin-bottom:10px}
.ck{color:#fff;font-weight:700;margin-left:8px}
.grid{display:grid;grid-template-columns:1fr 320px;
gap:20px}
@media(max-width:1100px){.grid{grid-template-columns:1fr}}
.wrap{overflow:auto;max-height:66vh;
border:1px solid #24262d;border-radius:3px}
table.b{border-collapse:collapse;width:100%}
table.b th{background:#101115;color:#878c96;
font-size:10px;letter-spacing:.06em;padding:6px 4px;
position:sticky;top:0;z-index:2;
border-bottom:1px solid #24262d}
table.b th.mine{color:#fff;background:#1c1f26}
th.rw{position:sticky;left:0;z-index:1;width:26px}
td.cl{border:1px solid #17191e;padding:4px 5px;
height:34px;min-width:92px;vertical-align:middle;
background:#0d0e11}
td.cl.mine{background:#131519}
td.cl.on{outline:2px solid #c3c9d4;
outline-offset:-2px;background:#1c1f26}
.nm{display:block;font-weight:600;font-size:12px;
margin-top:2px}
.tt{color:#6f747d;font-size:10px}
.pn{color:#5c6068}
table.s{width:100%;border-collapse:collapse}
table.s td{padding:5px 6px;
border-bottom:1px solid #17191e}
td.r{text-align:right;color:#a8aeb9}
td.sl{color:#878c96;font-size:10px;font-weight:700;
width:44px}
.pos{display:inline-block;min-width:30px;
text-align:center;padding:1px 5px;border-radius:2px;
font-size:9px;font-weight:800;color:#0a0a0c}
.QB{background:#f2f4f8}.RB{background:#d9dee6}
.WR{background:#c0c6d0}.TE{background:#a8aeb9}
.K{background:#9096a1}.DEF{background:#7d838e}
.you{color:#fff}
.big{font-size:24px;font-weight:700}
"""

def sel(i, opts, val=None):
    o = "".join("<option value='%s'%s>%s</option>"
                % (v, " selected" if v == val else "", t)
                for v, t in opts)
    return "<select id=%s>%s</select>" % (i, o)

BAR = ("<div class=cfg>"
       "<div class=fld><label>Scoring</label>"
       + sel("sc", [("g", "Full PPR"),
                    ("gh", "Half PPR"),
                    ("gs", "Standard")]) + "</div>"
       "<div class=fld><label>Draft type</label>"
       + sel("dt", [("snake", "Snake"),
                    ("linear", "Linear")]) + "</div>"
       "<div class=fld><label>Opponents</label>"
       + sel("op", [("basic", "ADP basic"),
                    ("adv", "VORP advanced")]) + "</div>"
       "<div class=fld><label>Teams</label>"
       + sel("nt", [(str(n), str(n))
                    for n in (8, 10, 12, 14)], "12")
       + "</div>"
       "<div class=fld><label>Your slot</label>"
       "<select id=sl></select></div>"
       "<div class=fld><label>&nbsp;</label>"
       "<button id=rnd>Randomize</button></div>"
       "<div class=fld><label>Pick clock</label>"
       + sel("pc", [("0", "None"), ("30", "30s"),
                    ("60", "60s")]) + "</div>"
       "<div class=fld><label>&nbsp;</label>"
       "<button id=go>Start draft</button></div>"
       "</div>")

js = open("site/_mock.js").read().replace(
    "__DATA__", json.dumps(P), 1)
H = ("<!doctype html><html><head><meta charset=utf-8>"
     "<meta name=viewport content='width=device-width,"
     "initial-scale=1'><title>Mock Draft</title><style>"
     + CSS + "</style></head><body><div class=w>"
     "<h1>Mock Draft</h1>" + BAR
     + "<div id=st></div><div class=grid><div>"
     "<div class=wrap><table class=b><tbody id=bd>"
     "</tbody></table></div>"
     "<h2>Best available</h2>"
     "<div class=bar style='display:flex;gap:8px;"
     "margin-bottom:6px'>"
     "<input id=s placeholder='search player'>"
     "<select id=f><option value=''>all</option>"
     "<option>QB</option><option>RB</option>"
     "<option>WR</option><option>TE</option>"
     "<option>K</option><option>DEF</option>"
     "</select></div>"
     "<table class=s><tbody id=av></tbody></table>"
     "</div><div>"
     "<h2>Your lineup &middot; <span class=big id=mt>"
     "0</span> ppg</h2>"
     "<table class=s><tbody id=me></tbody></table>"
     "<h2>Live standings</h2>"
     "<table class=s><tbody id=gr></tbody></table>"
     "</div></div></div><script>" + js
     + "</script></body></html>")
open("site/mock.html", "w").write(H)
print("\nwrote site/mock.html  %d KB" % (len(H) // 1024))
