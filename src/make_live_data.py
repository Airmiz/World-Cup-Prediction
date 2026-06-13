"""Export everything the in-browser live engine needs to website/live_data.json.

Contents:
- teams (group order), flags, groups
- group fixtures with an 8x8 truncated/renormalised score PMF (for sampling
  matches not yet played) plus id/city/utc kickoff
- 48x48 knockout win-probability matrices: P0 (neutral) and P1 (row team at
  home) — includes extra time + penalties
- Annex C map: sorted-8-letter combo -> group letters for the 8 third slots
- knockout structure (round_of_32 codes incl third_slot+venue; later rounds
  feeders+venue) and knockout kickoffs (utc+city)
- pre-tournament baseline advancement/title probabilities (for live deltas)
- a snapshot of results already played (offline fallback)
"""
import json
import numpy as np
import pandas as pd

from simulate import build_model, ko_win_tables
from model import score_matrix, outcome_probs
from make_site import et_to_utc, CITY_TZ   # reuse kickoff conversion

G = 8  # truncate goals to 0..7

df, ratings, dc, eg, w = build_model()
tj = json.load(open("data/tournament.json"))
groups = tj["groups"]
GROUPS = "ABCDEFGHIJKL"
teams = [t for g in GROUPS for t in groups[g]]
tp = pd.read_csv("output/team_probabilities.csv").set_index("team")
mp = pd.read_csv("output/match_predictions.csv")

# ---- group fixtures + PMFs ----
from simulate import pair_lambdas
fix = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= "2026-06-01")].reset_index(drop=True)
group_of = {t: g for g, ts in groups.items() for t in ts}
utc_by_pair = {(r.home_team, r.away_team): r.utc_kickoff for r in mp.itertuples()}
city_by_pair = {(r.home_team, r.away_team): r.city for r in mp.itertuples()}
eg_by_pair = {(r.home_team, r.away_team): (float(r.exp_goals_home), float(r.exp_goals_away)) for r in mp.itertuples()}

fixtures = []
for k, r in fix.iterrows():
    home_adv = str(r["neutral"]).upper() != "TRUE"
    lh, la = pair_lambdas(dc, eg, ratings, w, r["home_team"], r["away_team"], home_adv)
    P = score_matrix(lh, la, dc.rho)[:G, :G]
    P = P / P.sum()
    eh, ea = eg_by_pair.get((r["home_team"], r["away_team"]), (lh, la))
    fixtures.append({
        "id": k, "group": group_of[r["home_team"]],
        "home": r["home_team"], "away": r["away_team"],
        "city": city_by_pair.get((r["home_team"], r["away_team"]), r["city"]),
        "utc": utc_by_pair.get((r["home_team"], r["away_team"]), ""),
        "eh": round(eh, 3), "ea": round(ea, 3),
        "pmf": [round(float(x), 6) for x in P.ravel()],
    })

# ---- KO win matrices ----
P0, P1 = ko_win_tables(teams, dc, eg, ratings, w)
P0 = np.round(P0, 5).tolist()
P1 = np.round(P1, 5).tolist()

# ---- Annex C ----
ac = pd.read_csv("data/annex_c.csv")
slots = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]
annex = {r["combo"]: [r[s] for s in slots] for _, r in ac.iterrows()}

# ---- KO kickoffs ----
ko = pd.read_csv("data/kickoffs_ko.csv")
ko_times = {str(int(r.match)): {"utc": et_to_utc(r.date, r.et, r.city), "city": r.city}
            for r in ko.itertuples()}

# ---- baseline probabilities ----
base_cols = ["p_reach_r32", "p_reach_r16", "p_reach_qf", "p_reach_sf", "p_reach_final", "p_champion"]
baseline = {t: {c: round(float(tp.loc[t, c]), 5) for c in base_cols} for t in teams}

# ---- snapshot of played matches ----
played = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= "2026-06-01")
            & df["home_score"].notna()]
snapshot = [{"date": r["date"].strftime("%Y-%m-%d"), "home": r["home_team"], "away": r["away_team"],
             "hs": int(r["home_score"]), "as": int(r["away_score"])} for _, r in played.iterrows()]

from make_site import FLAGS

# known goal minutes for played matches (keyed "home|away"); enables real win-prob replay.
# Maintained in data/goal_events.json so the scheduled live-refresh job can append to it.
import os
goal_events = json.load(open("data/goal_events.json")) if os.path.exists("data/goal_events.json") else {}

# ---- team detail: info, all-time head-to-head, recent form (from 1872-2026 DB) ----
teamset = set(teams)
hist = df.dropna(subset=["home_score"]).copy()
hist["home_score"] = hist["home_score"].astype(int)
hist["away_score"] = hist["away_score"].astype(int)
h2h = {t: {} for t in teams}
both = hist[hist["home_team"].isin(teamset) & hist["away_team"].isin(teamset)]
for r in both.itertuples():
    for x, y, xs, ys in ((r.home_team, r.away_team, r.home_score, r.away_score),
                         (r.away_team, r.home_team, r.away_score, r.home_score)):
        rec = h2h[x].setdefault(y, [0, 0, 0, 0, 0])   # w, d, l, gf, ga
        rec[0 if xs > ys else (1 if xs == ys else 2)] += 1
        rec[3] += xs; rec[4] += ys
form = {}
hist_sorted = hist.sort_values("date")
for t in teams:
    sub = hist_sorted[(hist_sorted["home_team"] == t) | (hist_sorted["away_team"] == t)].tail(6)
    fl = []
    for r in sub.itertuples():
        if r.home_team == t:
            opp, gf, ga = r.away_team, r.home_score, r.away_score
        else:
            opp, gf, ga = r.home_team, r.away_score, r.home_score
        fl.append({"opp": opp, "gf": gf, "ga": ga,
                   "res": "W" if gf > ga else ("D" if gf == ga else "L")})
    form[t] = fl
teaminfo = {t: {"group": tp.loc[t, "group"], "elo": round(float(tp.loc[t, "elo"])),
                "attack": round(float(tp.loc[t, "dc_attack"]), 2),
                "defence": round(float(tp.loc[t, "dc_defence"]), 2)} for t in teams}

import os as _os
lineups = json.load(open("data/lineups.json")) if _os.path.exists("data/lineups.json") else {}
odds_history = json.load(open("data/odds_history.json")) if _os.path.exists("data/odds_history.json") else []

data = {
    "generated_utc": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
    "flags": FLAGS, "goal_events": goal_events, "lineups": lineups, "odds_history": odds_history,
    "h2h": h2h, "form": form, "teaminfo": teaminfo,
    "groups": groups, "group_order": GROUPS, "teams": teams,
    "third_slots": slots,
    "fixtures": fixtures, "grid": G,
    "ko_struct": {"r32": tj["round_of_32"], "r16": tj["round_of_16"],
                  "qf": tj["quarterfinals"], "sf": tj["semifinals"], "final": tj["final"]},
    "ko_times": ko_times,
    "P0": P0, "P1": P1,
    "annex": annex,
    "baseline": baseline,
    "snapshot": snapshot,
    "hosts": ["United States", "Mexico", "Canada"],
}
json.dump(data, open("website/live_data.json", "w"))
sz = len(json.dumps(data)) / 1024
print(f"live_data.json written ({sz:.0f} KB); fixtures={len(fixtures)}, played={len(snapshot)}")
