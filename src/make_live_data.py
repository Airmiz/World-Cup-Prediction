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

# ---- betting-market integration (Egidi, Pauli & Torelli 2018) ----
# The closing line is the hardest benchmark to beat; convex-blending the model's
# goal-rates toward odds-implied goal-rates yields bookmaker-grade forecasts.
import os as _osm
from scipy.optimize import minimize as _minimize
MARKET = json.load(open("data/odds_market.json")) if _osm.path.exists("data/odds_market.json") else {}
# Weight on the market in the model<->market blend (0 = model only, 1 = market only).
# DISABLED (0.0): a retrospective backtest on the played WC matches showed the blend did
# NOT improve accuracy — the model is currently out-scoring the bookmakers (model RPS 0.180
# vs market 0.206; blend@0.5 0.191), so per the only-ship-if-it-improves rule it stays off.
# The odds are still captured and shown (model vs market scorecard); raise this once/if the
# market starts beating the model over a larger sample.
BLEND_W = 0.0

def implied_lambdas(pH, pD, pA, rho, guess=(1.3, 1.3)):
    """Recover home/away Poisson goal-rates whose Dixon-Coles outcome probs match the market line."""
    tgt = np.array([pH, pD, pA])
    def loss(x):
        lh, la = np.exp(x)
        p = np.array(outcome_probs(score_matrix(lh, la, rho)))
        return float(np.sum((p - tgt) ** 2))
    r = _minimize(loss, np.log(np.maximum(guess, 0.2)), method="Nelder-Mead",
                  options={"xatol": 1e-4, "fatol": 1e-9, "maxiter": 500})
    lh, la = np.exp(r.x)
    return float(lh), float(la)

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

# ---- knockout bracket resolution (groups complete -> deterministic) so KO fixtures get a
#      proper round + kickoff instead of a leftover group letter, and can lock into the bracket ----
group_pairs = set(utc_by_pair.keys())            # the 72 group fixtures (home,away)
KT = {str(int(r.match)): {"utc": et_to_utc(r.date, r.et, r.city), "city": r.city}
      for r in pd.read_csv("data/kickoffs_ko.csv").itertuples()}
_acx = pd.read_csv("data/annex_c.csv")
_slots = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]
_annex = {row["combo"]: [row[s] for s in _slots] for _, row in _acx.iterrows()}
KO = {"r32": tj["round_of_32"], "r16": tj["round_of_16"], "qf": tj["quarterfinals"],
      "sf": tj["semifinals"], "final": tj["final"]}

def _break_tie(block, pts, gd, gf, pgf):
    if len(block) < 2: return list(block)
    mp_ = {t: 0 for t in block}; mg = {t: 0 for t in block}; mf = {t: 0 for t in block}
    for x in range(len(block)):
        for y in range(x + 1, len(block)):
            a, b = block[x], block[y]; ga = pgf.get((a, b)); gb = pgf.get((b, a))
            if ga is None or gb is None: continue
            mf[a] += ga; mf[b] += gb; mg[a] += ga - gb; mg[b] += gb - ga
            if ga > gb: mp_[a] += 3
            elif gb > ga: mp_[b] += 3
            else: mp_[a] += 1; mp_[b] += 1
    s = sorted(block, key=lambda t: (-mp_[t], -mg[t], -mf[t], -gd[t], -gf[t]))
    out = []; i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and (mp_[s[j+1]], mg[s[j+1]], mf[s[j+1]]) == (mp_[s[i]], mg[s[i]], mf[s[i]]): j += 1
        sub = s[i:j+1]
        out += _break_tie(sub, pts, gd, gf, pgf) if 1 < len(sub) < len(block) else sub
        i = j + 1
    return out

def _group_standings():
    res = {(r.home_team, r.away_team): (int(r.home_score), int(r.away_score))
           for r in fix.itertuples() if (r.home_team, r.away_team) in group_pairs and pd.notna(r.home_score)}
    st = {}
    for g, ts in groups.items():
        pts = {t: 0 for t in ts}; gd = {t: 0 for t in ts}; gf = {t: 0 for t in ts}; pgf = {}
        for (h, a), (hs, as_) in res.items():
            if h in ts and a in ts:
                pts[h] += 3 if hs > as_ else (1 if hs == as_ else 0); pts[a] += 3 if as_ > hs else (1 if hs == as_ else 0)
                gd[h] += hs - as_; gd[a] += as_ - hs; gf[h] += hs; gf[a] += as_; pgf[(h, a)] = hs; pgf[(a, h)] = as_
        arr = sorted(ts, key=lambda t: -pts[t]); order = []; i = 0
        while i < len(arr):
            j = i
            while j + 1 < len(arr) and pts[arr[j+1]] == pts[arr[i]]: j += 1
            order += _break_tie(arr[i:j+1], pts, gd, gf, pgf); i = j + 1
        st[g] = {"order": order, "pts": pts, "gd": gd, "gf": gf}
    return st

KO_TEAMS = {}; ROUND_OF = {}
_LATER = [("r16", "Round of 16"), ("qf", "Quarterfinal"), ("sf", "Semifinal"), ("final", "Final")]
for rk, label in [("r32", "Round of 32")] + _LATER:
    for mno in KO[rk]: ROUND_OF[mno] = label
_grp_done = sum(1 for r in fix.itertuples()
                if (r.home_team, r.away_team) in group_pairs and pd.notna(r.home_score)) == 72
if _grp_done:
    st = _group_standings()
    winners = {g: st[g]["order"][0] for g in groups}; runners = {g: st[g]["order"][1] for g in groups}
    thirds = {g: st[g]["order"][2] for g in groups}
    qg = sorted(groups, key=lambda g: (-st[g]["pts"][thirds[g]], -st[g]["gd"][thirds[g]], -st[g]["gf"][thirds[g]]))[:8]
    slot_group = dict(zip(_slots, _annex.get("".join(sorted(qg)), [])))
    def _code(code, info):
        if code == "3rd": return thirds.get(slot_group.get(info.get("third_slot")))
        return (winners if code[0] == "1" else runners).get(code[1])
    for mno, info in KO["r32"].items():
        KO_TEAMS[mno] = (_code(info["home"], info), _code(info["away"], info))

def _subtree(mno):
    if mno in KO["r32"]: return set(t for t in KO_TEAMS.get(mno, ()) if t)
    for rk, _ in _LATER:
        if mno in KO[rk]: f1, f2, _v = KO[rk][mno]; return _subtree(f1) | _subtree(f2)
    return set()

def _find_ko(a, b):
    for mno, (t1, t2) in KO_TEAMS.items():
        if {a, b} == {t1, t2}: return mno
    for rk, _ in _LATER:
        for mno, (f1, f2, _v) in KO.get(rk, {}).items():
            s1, s2 = _subtree(f1), _subtree(f2)
            if (a in s1 and b in s2) or (a in s2 and b in s1): return mno
    return None

fixtures = []
n_blended = 0
for k, r in fix.iterrows():
    home_adv = str(r["neutral"]).upper() != "TRUE"
    lh, la = pair_lambdas(dc, eg, ratings, w, r["home_team"], r["away_team"], home_adv)
    model_hda = [round(float(x), 4) for x in outcome_probs(score_matrix(lh, la, dc.rho))]
    mkt = MARKET.get(r["home_team"] + "|" + r["away_team"])
    rec_extra = {"hda_model": model_hda}
    if mkt:
        rec_extra["hda_market"] = [mkt["h"], mkt["d"], mkt["a"]]
        rec_extra["mkt_prov"] = mkt.get("prov", "Market")
        if BLEND_W > 0:   # blend the model's goal-rates toward the odds-implied rates (off by default)
            mlh, mla = implied_lambdas(mkt["h"], mkt["d"], mkt["a"], dc.rho, guess=(lh, la))
            lh = float(np.exp((1 - BLEND_W) * np.log(lh) + BLEND_W * np.log(max(mlh, 1e-3))))
            la = float(np.exp((1 - BLEND_W) * np.log(la) + BLEND_W * np.log(max(mla, 1e-3))))
            rec_extra["blended"] = True
            n_blended += 1
    P = score_matrix(lh, la, dc.rho)[:G, :G]
    P = P / P.sum()
    rec_extra["hda"] = [round(float(x), 4) for x in outcome_probs(score_matrix(lh, la, dc.rho))]
    is_ko = (r["home_team"], r["away_team"]) not in group_pairs
    if is_ko:                                   # knockout: round + bracket-slot kickoff, no group letter
        mno = _find_ko(r["home_team"], r["away_team"])
        kt = KT.get(mno) if mno else None
        rec_extra["group"] = None
        rec_extra["round"] = ROUND_OF.get(mno, "Knockout")
        rec_extra["ko"] = mno          # bracket match number, for locking the result into the bracket
        city = kt["city"] if kt else r["city"]
        utc = kt["utc"] if kt else ""
    else:
        rec_extra["group"] = group_of[r["home_team"]]
        city = city_by_pair.get((r["home_team"], r["away_team"]), r["city"])
        utc = utc_by_pair.get((r["home_team"], r["away_team"]), "")
    fixtures.append({
        "id": k, "home": r["home_team"], "away": r["away_team"], "city": city, "utc": utc,
        "eh": round(float(lh), 3), "ea": round(float(la), 3),   # blended expected goals
        "pmf": [round(float(x), 6) for x in P.ravel()],
        **rec_extra,
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
