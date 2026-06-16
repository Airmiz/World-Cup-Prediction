#!/usr/bin/env bash
# Live refresh: pull latest results, refit the model to today, regenerate pages.
# Goal-minute fetching for new matches is done by the scheduled agent (needs web).
set -euo pipefail
cd "$(dirname "$0")/.."

TODAY=$(date -u +%Y-%m-%d)
echo "[refresh] $(date -u) cutoff=$TODAY"

# 1. latest results
curl -sL --max-time 60 -o data/results.csv \
  https://raw.githubusercontent.com/martj42/international_results/master/results.csv
PLAYED=$(python3 - <<'PY'
import pandas as pd
df=pd.read_csv("data/results.csv"); df["date"]=pd.to_datetime(df["date"])
wc=df[(df.tournament=="FIFA World Cup")&(df.date>="2026-06-01")&df.home_score.notna()]
print(len(wc))
PY
)
echo "[refresh] WC2026 matches played: $PLAYED"

# 2. fetch real goal minutes for newly played matches (openfootball; no key needed)
python3 src/fetch_goals.py || echo "[refresh] goal fetch skipped"

# 2b. fetch lineups/formations/cards/subs.
#     ESPN JSON API (free, richest: formations + stats) is preferred; then optional paid keys; Wikipedia as last resort.
python3 src/fetch_espn.py || echo "[refresh] espn fetch skipped"
# 2b'. pre-match betting-market odds for upcoming fixtures (powers the model<->market blend)
python3 src/fetch_odds.py || echo "[refresh] odds fetch skipped"
python3 src/fetch_fdorg.py || echo "[refresh] fd.org fetch skipped"
python3 src/fetch_squad.py || echo "[refresh] squad fetch skipped"
# 2c. free fallback: pull lineups/cards/subs from Wikipedia (no key; best-effort, lags live)
python3 src/fetch_wiki.py || echo "[refresh] wiki fetch skipped"

# 3. refit model to today's data + regenerate engine data and pages
export WC_CUTOFF="$TODAY"
python3 src/make_live_data.py
# 3b. Forecast Tracker: snapshot today's championship odds, then re-embed history
node src/snapshot.js || echo "[refresh] snapshot skipped"
python3 src/make_live_data.py
python3 src/make_live.py
python3 src/make_site.py
echo "[refresh] done — pages regenerated"
