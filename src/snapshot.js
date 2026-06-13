/* Forecast Tracker snapshot (runs in the cloud job via Node).
 * Reuses the exact in-browser Monte Carlo engine to compute current championship
 * probabilities conditioned on results played, and appends today's snapshot to
 * data/odds_history.json (deduped by date). Seeds a pre-tournament baseline point
 * so the chart has a line from day one.
 */
const fs = require("fs");
const path = require("path");
const { WCLive } = require("./live_engine.js");

const ROOT = path.join(__dirname, "..");
const D = JSON.parse(fs.readFileSync(path.join(ROOT, "website/live_data.json"), "utf8"));
const HIST = path.join(ROOT, "data/odds_history.json");
const TOPN = 16, N = 30000;

// --- played results from the same CSV the live page uses ---
function parseResults() {
  const txt = fs.readFileSync(path.join(ROOT, "data/results.csv"), "utf8");
  const lines = txt.split(/\r?\n/).filter(Boolean);
  const head = lines[0].split(",");
  const ix = n => head.indexOf(n);
  const di = ix("date"), hi = ix("home_team"), ai = ix("away_team"),
        hsi = ix("home_score"), asi = ix("away_score"), ti = ix("tournament");
  const fixByPair = {}; D.fixtures.forEach(f => fixByPair[f.home + "|" + f.away] = f.id);
  const results = {};
  for (let i = 1; i < lines.length; i++) {
    const c = lines[i].split(",");
    if (c[ti] !== "FIFA World Cup" || c[di] < "2026-06-01") continue;
    if (c[hsi] === "" || c[hsi] == null || isNaN(+c[hsi])) continue;
    const id = fixByPair[c[hi] + "|" + c[ai]];
    if (id != null) results[id] = [+c[hsi], +c[asi]];
  }
  return results;
}

function topProbs(champ) {
  const e = Object.entries(champ).sort((a, b) => b[1] - a[1]).slice(0, TOPN);
  const o = {}; e.forEach(([t, p]) => o[t] = Math.round(p * 1e4) / 1e4); return o;
}

function main() {
  let hist = [];
  if (fs.existsSync(HIST)) { try { hist = JSON.parse(fs.readFileSync(HIST, "utf8")); } catch (e) {} }
  // seed pre-tournament baseline (once)
  if (!hist.some(h => h.date === "2026-06-11")) {
    const base = {}; for (const t in D.baseline) base[t] = D.baseline[t].p_champion;
    hist.push({ date: "2026-06-11", champ: topProbs(base) });
  }
  const results = parseResults();
  const out = WCLive.runLive(D, { N, results });
  const today = new Date().toISOString().slice(0, 10);
  hist = hist.filter(h => h.date !== today);            // dedupe today
  hist.push({ date: today, champ: topProbs(out.champion) });
  hist.sort((a, b) => a.date.localeCompare(b.date));
  fs.writeFileSync(HIST, JSON.stringify(hist, null, 1));
  const top = Object.entries(out.champion).sort((a, b) => b[1] - a[1]).slice(0, 4)
    .map(([t, p]) => `${t} ${(p * 100).toFixed(1)}%`).join(", ");
  console.log(`[snapshot] ${today}: ${Object.keys(results).length} results · top: ${top} · ${hist.length} history points`);
}
main();
