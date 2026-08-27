import json, ssl, urllib.request, pandas as pd
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    CTX = ssl.create_default_context()

UA = {"User-Agent": "VaporAI/1.0 (personal fantasy tool)",
      "Accept": "application/rss+xml, application/xml, text/xml"}

FEEDS = [("CBS NFL", "https://www.cbssports.com/rss/headlines/nfl/")]

BREAK = ["source", "trade", "traded", "sign", "suspend", "release",
         "waive", "activat", "injur", "out for", "placed on", "ir",
         "acquire", "claim"]
DC = "{http://purl.org/dc/elements/1.1/}creator"

def txt(node):
    if node is None or node.text is None:
        return ""
    return " ".join(node.text.split())

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return r.read()

arts, seen = [], set()
for tag, url in FEEDS:
    try:
        root = ET.fromstring(fetch(url))
    except Exception as e:
        print("  FEED FAILED %-9s %s" % (tag, e))
        continue
    items = root.findall(".//item")
    print("  %-9s %d items" % (tag, len(items)))
    for it in items:
        hd = txt(it.find("title"))
        link = txt(it.find("link"))
        if not hd or link in seen:
            continue
        seen.add(link)
        try:
            ts = parsedate_to_datetime(
                txt(it.find("pubDate"))).strftime("%Y-%m-%dT%H:%MZ")
        except Exception:
            ts = ""
        enc = it.find("enclosure")
        img = enc.get("url") if enc is not None else ""
        low = hd.lower()
        arts.append({"hd": hd, "dk": txt(it.find("description")),
                     "by": txt(it.find(DC)), "ts": ts, "url": link,
                     "img": img or "", "src": tag,
                     "ins": any(k in low for k in BREAK),
                     "trade": "trad" in low})

arts.sort(key=lambda x: x["ts"], reverse=True)
print("\narticles: %d | breaking-flagged: %d | trade-related: %d"
      % (len(arts), sum(a["ins"] for a in arts),
         sum(a["trade"] for a in arts)))
print("\n--- 8 most recent ---")
for a in arts[:8]:
    print("  %s %-8s %s"
          % (a["ts"][:10], "BREAK" if a["ins"] else "", a["hd"][:60]))

TRADES = []
try:
    import nflreadpy as nfl
    t = nfl.load_trades()
    t = t.to_pandas() if hasattr(t, "to_pandas") else t
    t = t[t["season"] >= 2026] if "season" in t.columns else t
    t = t.dropna(subset=["pfr_name"]) if "pfr_name" in t.columns else t
    print("\n2026 player-trade rows: %d" % len(t))
    if len(t):
        keep = [c for c in ["trade_date", "gave", "received",
                            "pfr_name", "pick_round"] if c in t.columns]
        TRADES = t[keep].fillna("").astype(str).to_dict("records")[:80]
        print(t[keep].head(10).to_string(index=False))
except Exception as e:
    print("\nload_trades unavailable: %s" % e)

MOVES = []
try:
    H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
    R = pd.read_csv("rosters_2026.csv", low_memory=False)
    tc = "team" if "team" in H.columns else "recent_team"
    last = H[H["season"] == 2025].sort_values(["season", "week"])
    last = last.groupby("player_id").tail(1)[
        ["player_id", "player_display_name", "position", tc]]
    last = last.rename(columns={tc: "from_tm"})
    cur = R[["gsis_id", "team"]].dropna(subset=["gsis_id"])
    cur = cur.rename(columns={"gsis_id": "player_id", "team": "to_tm"})
    cur = cur.drop_duplicates("player_id")
    m = last.merge(cur, on="player_id")
    m = m[m["from_tm"] != m["to_tm"]]
    m = m[m["position"].isin(["QB", "RB", "WR", "TE"])]
    B = pd.read_csv("board_final.csv", low_memory=False)
    B = B[["player_display_name", "rank", "points"]].rename(
        columns={"player_display_name": "nm"})
    m = m.merge(B, left_on="player_display_name", right_on="nm",
                how="left").drop(columns=["nm"])
    m = m.sort_values("rank", na_position="last")
    m.to_csv("moves_2026.csv", index=False)
    MOVES = m.head(60).fillna("").to_dict("records")
    print("\nskill players who changed teams: %d" % len(m))
except Exception as e:
    print("\nmovement table failed: %s" % e)

OUT = {"articles": arts, "moves": MOVES, "trades": TRADES,
       "built": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%MZ")}
with open("news_2026.json", "w") as f:
    json.dump(OUT, f, separators=(",", ":"))
print("\nSaved news_2026.json  (%d articles, %d moves, %d trades)"
      % (len(arts), len(MOVES), len(TRADES)))
