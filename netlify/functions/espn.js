// CORS proxy for ESPN's fantasy read API.
// Public leagues need no credentials.
// Private leagues: set ESPN_S2 and ESPN_SWID as
// Netlify environment variables. Never commit them.
const HOST = "https://lm-api-reads.fantasy.espn.com";
const PATH = "/apis/v3/games/ffl/seasons";

const OKVIEWS = new Set([
  "mTeam", "mRoster", "mSettings", "mMatchup",
  "mMatchupScore", "mNav", "mStandings", "mDraftDetail"
]);

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Content-Type": "application/json"
};

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers: CORS, body: "" };
  }
  const q = event.queryStringParameters || {};

  // Hard-sanitize: only digits reach the URL.
  const lid = String(q.league || "").replace(/\D/g, "");
  const yr = String(q.year || "2026").replace(/\D/g, "");
  if (!lid) {
    return {
      statusCode: 400, headers: CORS,
      body: JSON.stringify({ error: "missing league id" })
    };
  }

  // Whitelist views so this can't be an open proxy.
  let views = String(q.views || "mTeam,mSettings")
    .split(",").map(s => s.trim())
    .filter(v => OKVIEWS.has(v));
  if (!views.length) views = ["mTeam", "mSettings"];

  let url = HOST + PATH + "/" + yr
    + "/segments/0/leagues/" + lid
    + "?" + views.map(v => "view=" + v).join("&");

  const wk = String(q.week || "").replace(/\D/g, "");
  if (wk) url += "&scoringPeriodId=" + wk;

  const headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X "
      + "10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
  };

  // Private-league cookies come from the environment only.
  const s2 = process.env.ESPN_S2;
  const swid = process.env.ESPN_SWID;
  if (s2 && swid) {
    headers.Cookie = "espn_s2=" + s2 + "; SWID=" + swid;
  }

  try {
    const r = await fetch(url, { headers });
    const txt = await r.text();
    if (!r.ok) {
      return {
        statusCode: r.status, headers: CORS,
        body: JSON.stringify({
          error: "espn " + r.status,
          hint: r.status === 401
            ? "private league: set ESPN_S2 and ESPN_SWID"
            : "check the league id and season",
          detail: txt.slice(0, 300)
        })
      };
    }
    return {
      statusCode: 200,
      headers: Object.assign({}, CORS, {
        "Cache-Control": "public, max-age=60"
      }),
      body: txt
    };
  } catch (e) {
    return {
      statusCode: 502, headers: CORS,
      body: JSON.stringify({ error: String(e).slice(0, 200) })
    };
  }
};
