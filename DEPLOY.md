# Put the live page online — fully automatic, computer off

Goal: the page lives at a public URL and updates itself — scores, odds, bracket,
**and real goal-minute win-probability charts** — without your computer being on.

This uses **GitHub** (stores the project + runs a free cloud job) + **Netlify**
(hosts the page, auto-publishes on every update). One-time setup ≈ 15 minutes.

## How it stays live without your machine

| Layer | What it does | Runs where |
|---|---|---|
| Browser fetch (every 90s) | scores, standings, odds, bracket | the visitor's browser |
| GitHub Actions (every 2h) | pull results + **real goal minutes**, refit model, rebuild, commit | GitHub's cloud |
| Netlify | publishes the new files the instant GitHub updates | Netlify's cloud |

Goal minutes come automatically from the open **openfootball** dataset (no API key),
so each finished match's win-probability chart replays the real goals on its own.

## One-time setup

1. **GitHub account** → create a repo, e.g. `world-cup-2026` (Public is fine).

2. **Upload this whole folder** to the repo (include the hidden `.github` folder).
   With git:
   ```
   cd "World Cup Prediction"
   git init && git add -A && git commit -m "World Cup 2026 live"
   git branch -M main
   git remote add origin https://github.com/<you>/world-cup-2026.git
   git push -u origin main
   ```

3. **Connect Netlify to the repo:** netlify.com → *Add new site → Import an existing
   project → GitHub →* pick `world-cup-2026`. Set:
   - **Build command:** *(leave empty)*
   - **Publish directory:** `website`

   Click Deploy. Your live URL is shown when it finishes, e.g.
   `https://your-name.netlify.app` — the live page is at that URL + `/live.html`.
   Every time the cloud job commits an update, Netlify republishes automatically.

4. **Confirm the cloud job is on:** GitHub repo → *Actions* tab → enable workflows if
   prompted. It runs every 2 hours; you can also click *Run workflow* to trigger it now.

Done. From here it's hands-off: results, model, and real goal timelines all refresh in
the cloud, Netlify republishes, and your computer is never involved.

## Knobs

- **Cadence:** edit `.github/workflows/refresh.yml` → `cron:` (e.g. `0 * * * *` hourly).
- **Force a refresh now:** Actions tab → *Run workflow*.
- **Drag-and-drop instead?** You can still drag the `website/` folder onto
  netlify.com/drop for instant hosting — you just won't get the automatic cloud
  refresh (scores still self-update in the browser; goal timelines/model won't).

## Optional: unlock formations, cards, subs & full-squad ratings

The Match Centre shows our player ratings, goal log and result-vs-model from free data.
To also fill in **formations, lineups, cards, substitutions and full-squad ratings**, add
a free **API-Football** key (no card required):

1. Sign up at **dashboard.api-football.com** (or api-sports.io) → copy your API key.
2. In your GitHub repo: **Settings → Secrets and variables → Actions → New repository
   secret**. Name it exactly `API_FOOTBALL_KEY`, paste the key, save.
3. That's it. On the next cloud run, `src/fetch_squad.py` pulls lineups/cards/subs into
   `data/lineups.json`, and the Match Centre fills them in automatically. Without the
   key, those sections simply stay hidden (never faked). Free tier is ~100 requests/day,
   which the script stays within by caching finished matches.

## What each piece is

- `src/refresh.sh` — the one command the cloud job runs: pull results → fetch goal
  minutes (`src/fetch_goals.py`) → refit model → regenerate `website/`.
- `src/fetch_goals.py` — pulls real goal minutes from openfootball, merges into
  `data/goal_events.json` (hand-verified entries are preserved).
- `.github/workflows/refresh.yml` — the cloud schedule; commits updates so Netlify deploys.
