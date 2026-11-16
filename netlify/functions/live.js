// Live injury layer. The projection model is rebuilt at
// deploy time; this recomputes only what actually changes
// during the day -- designations, QB status and the target
// share they vacate. Cached 10 minutes at the edge.
const SLEEPER = "https://api.sleeper.app/v1/players/nfl";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Content-Type": "application/json",
  "Cache-Control": "public, max-age=600"
};

// measured in 460_qbinj.py over 1471 starts
const QB = { att: 0.842, ypa: 0.891, tdr: 0.710 };
// probability a designation still plays
const PLAY = { Out: 0, IR: 0, PUP: 0, Sus: 0, NA: 0,
               Doubtful: 0.15, Questionable: 0.75 };
// measured availability multipliers for the player himself
const SELF = { Out: 0, IR: 0, PUP: 0, Sus: 0, NA: 0,
               Doubtful: 0.35, Questionable: 0.88 };

let CACHE = null, AT = 0;

exports.handler = async () => {
  const now = Date.now();
  if (CACHE && now - AT < 600000) {
    return { statusCode: 200, headers: CORS, body: CACHE };
  }
  try {
    const r = await fetch(SLEEPER);
    const all = await r.json();

    const hurt = {};
    const byTeam = {};
    for (const id in all) {
      const p = all[id];
      if (!p || !p.team) continue;
      const pos = p.position;
      if (["QB", "RB", "WR", "TE"].indexOf(pos) < 0) continue;
      const st = p.injury_status;
      (byTeam[p.team] = byTeam[p.team] || []).push({
        id: id, n: p.full_name, pos: pos, st: st || "",
        depth: p.depth_chart_order || 99
      });
      if (st && st !== "Active") {
        hurt[norm(p.full_name)] = {
          n: p.full_name, tm: p.team, pos: pos,
          st: st, body: p.injury_body_part || "",
          note: (p.injury_notes || "").slice(0, 160),
          mult: (SELF[st] !== undefined) ? SELF[st] : 0.9
        };
      }
    }

    // QB1 hurt -> whole passing offence downgraded
    const teamAdj = {};
    for (const tm in byTeam) {
      const qbs = byTeam[tm]
        .filter(x => x.pos === "QB")
        .sort((a, b) => a.depth - b.depth);
      if (!qbs.length) continue;
      const q = qbs[0];
      const st = q.st;
      if (!st || st === "Active") continue;
      const p = (PLAY[st] !== undefined) ? PLAY[st] : 0.8;
      teamAdj[tm] = {
        qb: q.n, st: st, play: p,
        att: p + (1 - p) * QB.att,
        ypa: p + (1 - p) * QB.ypa,
        tdr: p + (1 - p) * QB.tdr
      };
    }

    const out = JSON.stringify({
      gen: new Date().toISOString(),
      hurt: hurt,
      team: teamAdj,
      counts: {
        players: Object.keys(hurt).length,
        teams: Object.keys(teamAdj).length
      }
    });
    CACHE = out; AT = now;
    return { statusCode: 200, headers: CORS, body: out };
  } catch (e) {
    return {
      statusCode: 502, headers: CORS,
      body: JSON.stringify({ error: String(e).slice(0, 200) })
    };
  }
};

function norm(s) {
  return String(s || "").toLowerCase()
    .replace(/[^a-z ]/g, "").replace(/\s+/g, " ").trim();
}
