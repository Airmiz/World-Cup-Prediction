# World Cup 2026 Statistical Forecast

A reproducible probabilistic model of the 2026 FIFA World Cup, frozen pre-tournament
(11 June 2026). Blends a time-decayed Dixon-Coles bivariate Poisson model with World
Football Elo ratings fitted on 49,477 internationals (1872–2026), validated
out-of-sample on the 2014/2018/2022 World Cups, and played through 200,000 Monte Carlo
simulations of the full 104-match tournament under FIFA's exact rules (including the
official Annex C third-place allocation, extra time, penalties, and venue-specific
host advantage).

## Headline results

Argentina 17.1% and Spain 15.7% lead the title race; England (6.4%) and France (6.3%)
head the chasing pack. Most likely final: Spain–Argentina (5.1%). Held-out 2022 log
loss 1.078 vs 1.099 uniform baseline, beating both standalone components.

## Folder contents

| Path | Contents |
|---|---|
| `data/results.csv` | International match history + 2026 fixtures (martj42/international_results) |
| `data/tournament.json` | Groups, bracket, knockout venues |
| `data/annex_c.csv` | FIFA's 495-row third-place allocation table (validated) |
| `data/kickoffs_et.csv` | Group-stage kickoff times (ET); converted to UTC into match_predictions.csv |
| `data/kickoffs_ko.csv` | Knockout-stage kickoff times/venues (M73–M104); localized on the bracket |
| `src/model.py` | Elo engine, Dixon-Coles MAP fit, Elo→goals GLM, blend |
| `src/backtest.py` | Walk-forward validation & hyperparameter tuning |
| `src/simulate.py` | Final fit + 200k tournament simulations |
| `src/figures.py`, `src/make_xlsx.py` | Charts and spreadsheet |
| `website/index.html` | Self-contained website: predicted bracket, all forecasts, methodology (double-click to open) |
| `website/live.html` | **Live page**: fetches real results, re-runs a Monte Carlo in-browser, updates standings/odds/bracket every 90s |
| `website/live_data.json` | Embedded engine data (score PMFs, 48×48 KO win matrix, Annex C, baseline) |
| `src/live_engine.js` | In-browser Monte Carlo engine (pure JS, conditions on played results) |
| `src/inplay.js` | In-play win-probability model (analytic Poisson) for the per-match chart |
| `src/fetch_goals.py` | Auto-pulls real goal minutes from openfootball into data/goal_events.json |
| `.github/workflows/refresh.yml` | Cloud cron (GitHub Actions) — auto-refresh + commit for Netlify |
| `DEPLOY.md` | How to host it fully-automatic (GitHub + Netlify, computer off) |
| `output/WC2026_report.docx` | Full methodology & results report |
| `output/WC2026_predictions.xlsx` | All match forecasts, team probabilities, validation |
| `output/*.csv`, `*.json` | Raw model artifacts |

## Reproduce

```bash
pip install numpy pandas scipy matplotlib openpyxl
python src/backtest.py    # validation + tuned hyperparameters
python src/simulate.py    # final model + 200,000 simulations (seed 20260611)
python src/figures.py
python src/make_xlsx.py
python src/bracket.py      # modal predicted bracket
python src/make_site.py    # regenerate website/index.html
python src/make_live_data.py  # export live engine data
python src/make_live.py    # regenerate website/live.html
```

## Live page

`website/live.html` runs the model **in the visitor's browser**. On load (and every
90s) it fetches the live results CSV from the open match database, locks in real
scores, and runs 20,000 conditional Monte-Carlo tournaments to refresh group
standings, title odds (with Δ vs the pre-tournament forecast), and a projected
bracket — no server required. If the feed is blocked it falls back to an embedded
snapshot. Remaining-match probabilities use the frozen pre-tournament model; to also
refresh the model's strengths on new results, re-run `make_live_data.py` (e.g. on a
daily schedule).

The live page also includes:
- **Tournament Stats** — Golden Boot, our cumulative player power rankings, storylines
  (biggest upset, most dramatic match, highest-scoring), and a **model scorecard**
  (live log-loss / Brier vs coin-flip baseline).
- **Title race** — a chart of each contender's championship probability over time,
  snapshotted daily by `src/snapshot.js` (reuses the engine in Node) into
  `data/odds_history.json`.
- **Team pages** — click any team in the title-odds table for live odds, recent form,
  and **all-time head-to-head** mined from the 1872–2026 results DB
  (`h2h`/`form`/`teaminfo` precomputed in `make_live_data.py`).
- **Score-forecast heatmap** on each match — the model's pre-match scoreline
  distribution with the actual result ringed.

Each live/finished match opens a **Match Centre**: our own player-rating model
(rates goal contributors from real events, crowns a Player of the Match), a goal
log (scorers/minutes/own-goals), and a "result vs model" panel. Add a free API-Football key (GitHub secret `API_FOOTBALL_KEY`, see DEPLOY.md) and
`src/fetch_squad.py` fills in **formations, lineups, cards, substitutions and
full-squad ratings** automatically; without it those sections stay hidden (never
fabricated). Upcoming matches show only pre-match odds — no invented scoreline.

Each live/finished match also has an **in-play win-probability chart** (`src/inplay.js`):
the three outcome probabilities across the 90 minutes, computed analytically (remaining
goals ~ Poisson(xG × time left)). Played matches replay their real goal timeline;
upcoming matches auto-simulate a plausible story. Scrub the minute, add/remove goals,
or re-simulate to explore.

To update mid-tournament: refresh `data/results.csv` from
github.com/martj42/international_results, set `CUTOFF` in `src/simulate.py` to
tomorrow, and re-run `simulate.py` (group matches already played will need their
actual results frozen in — see `simulate.py` notes).

## Model summary

Goal rates: λ = λ_DC^0.5 · λ_Elo^0.5. Dixon-Coles: attack/defence per team,
exponential decay ξ=0.7/yr, importance-weighted likelihood, Gaussian shrinkage,
ρ=−0.056 low-score coupling, home advantage +0.26 log-goals (hosts only).
Elo: K∈[20,60] by competition, goal-difference multiplier, +100 home; mapped to
goals via leakage-free Poisson regressions on pre-match ratings. Hyperparameters
tuned on WC 2014+2018 only; WC 2022 untouched holdout.
