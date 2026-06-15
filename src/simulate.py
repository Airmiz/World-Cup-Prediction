"""
Monte Carlo simulation of the 2026 FIFA World Cup (48 teams, 104 matches).

- Group stage: exact joint score PMFs per fixture (blended Dixon-Coles + Elo
  model), sampled S times; standings use FIFA tiebreakers (points, GD, GF,
  head-to-head for two-way ties, then a random key proxying conduct/ranking).
- Third-place teams: ranked across groups (points, GD, GF, random key); the
  best eight are slotted into the round of 32 using FIFA's official Annex C
  allocation table (all 495 combinations).
- Knockouts: single elimination with extra time (Poisson rates scaled by 1/3)
  and penalty shootouts (50/50); host-nation home advantage applied when a
  host plays a knockout match staged in its own country.
"""
from __future__ import annotations

import json
import numpy as np
import pandas as pd
from scipy.stats import poisson

from model import (load_results, run_elo, fit_dixon_coles, fit_elo_goals,
                   blend_lambdas, score_matrix, outcome_probs, MAX_G)

SEED = 20260611
N_SIMS = 200_000
import os
CUTOFF = pd.Timestamp(os.environ.get("WC_CUTOFF", "2026-06-11"))
GRID = MAX_G + 1
GROUPS = "ABCDEFGHIJKL"


def build_model():
    with open("output/backtest.json") as f:
        bt = json.load(f)["best"]
    xi, fw, w = bt["xi"], bt["friendly_w"], bt["blend_w"]
    df = load_results("data/results.csv")
    ratings, eh, ea = run_elo(df)
    dc = fit_dixon_coles(df, CUTOFF, xi=xi, friendly_w=fw)
    eg = fit_elo_goals(df, eh, ea, CUTOFF, xi=xi, friendly_w=fw)
    return df, ratings, dc, eg, w


def pair_lambdas(dc, eg, ratings, w, home, away, home_adv: bool):
    ldc = dc.lambdas(home, away, home_adv)
    lel = eg.lambdas(ratings.get(home, 1500.0), ratings.get(away, 1500.0), home_adv)
    return blend_lambdas(ldc, lel, w)


def ko_win_tables(teams, dc, eg, ratings, w):
    """P0[i,j] = P(i beats j after ET+pens, neutral); P1[i,j] = same with i at home."""
    n = len(teams)
    P0 = np.zeros((n, n)); P1 = np.zeros((n, n))
    for i, ti in enumerate(teams):
        for j, tj in enumerate(teams):
            if i == j:
                continue
            for adv, OUT in ((False, P0), (True, P1)):
                lh, la = pair_lambdas(dc, eg, ratings, w, ti, tj, adv)
                M90 = score_matrix(lh, la, dc.rho)
                p90h, p90d, _ = outcome_probs(M90)
                MET = score_matrix(lh / 3, la / 3, dc.rho)
                peth, petd, _ = outcome_probs(MET)
                OUT[i, j] = p90h + p90d * (peth + petd * 0.5)
    return P0, P1


def main():
    rng = np.random.default_rng(SEED)
    df, ratings, dc, eg, w = build_model()
    tj = json.load(open("data/tournament.json"))
    groups = tj["groups"]
    teams = [t for g in GROUPS for t in groups[g]]
    tidx = {t: k for k, t in enumerate(teams)}
    group_of = {t: g for g, ts in groups.items() for t in ts}
    host_country = np.array([t if t in ("United States", "Mexico", "Canada") else ""
                             for t in teams], dtype=object)

    # ---------------- fixtures & exact match-level predictions ----------------
    # Pre-tournament group-stage forecast: all 72 group fixtures (Jun 11-27),
    # whether or not they have since been played. Leakage is controlled by CUTOFF
    # in the model fit, not by hiding fixtures, so this stays correct mid-tournament.
    fix = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= "2026-06-01")
             & (df["date"] <= "2026-06-27")].reset_index(drop=True)
    assert len(fix) == 72, f"expected 72 group fixtures, got {len(fix)}"

    pmfs = np.zeros((72, GRID, GRID))
    match_rows = []
    for k, r in fix.iterrows():
        home_adv = str(r["neutral"]).upper() != "TRUE"
        lh, la = pair_lambdas(dc, eg, ratings, w, r["home_team"], r["away_team"], home_adv)
        P = score_matrix(lh, la, dc.rho)
        pmfs[k] = P
        pH, pD, pA = outcome_probs(P)
        flat = P.ravel()
        top = np.argsort(-flat)[:3]
        scores = [f"{t // GRID}-{t % GRID} ({flat[t]:.1%})" for t in top]
        match_rows.append({
            "date": r["date"].date().isoformat(), "group": group_of[r["home_team"]],
            "home_team": r["home_team"], "away_team": r["away_team"],
            "city": r["city"], "country": r["country"],
            "p_home_win": pH, "p_draw": pD, "p_away_win": pA,
            "exp_goals_home": lh, "exp_goals_away": la,
            "most_likely_scores": "; ".join(scores)})
    mpdf = pd.DataFrame(match_rows)
    # preserve kickoff columns (added downstream) so make_live_data/make_site keep working
    _mp = "output/match_predictions.csv"
    if os.path.exists(_mp):
        _prev = pd.read_csv(_mp)
        _kk = [c for c in ("utc_kickoff", "local_kickoff") if c in _prev.columns]
        if _kk:
            mpdf = mpdf.merge(_prev[["home_team", "away_team"] + _kk].drop_duplicates(
                ["home_team", "away_team"]), on=["home_team", "away_team"], how="left")
    mpdf.to_csv(_mp, index=False)

    # ---------------- sample group-stage scores ----------------
    S = N_SIMS
    HS = np.zeros((S, 72), dtype=np.int8)
    AS = np.zeros((S, 72), dtype=np.int8)
    for k in range(72):
        cdf = np.cumsum(pmfs[k].ravel())
        cdf[-1] = 1.0
        idx = np.searchsorted(cdf, rng.random(S))
        HS[:, k] = idx // GRID
        AS[:, k] = idx % GRID

    # ---------------- group standings ----------------
    # per group: local team order = groups[g], matches within group
    gmatch = {g: [] for g in GROUPS}   # (fixture_idx, local_home, local_away)
    for k, r in fix.iterrows():
        g = group_of[r["home_team"]]
        lh_ = groups[g].index(r["home_team"])
        la_ = groups[g].index(r["away_team"])
        gmatch[g].append((k, lh_, la_))

    winners = np.zeros((S, 12), dtype=np.int16)   # global team idx
    runners = np.zeros((S, 12), dtype=np.int16)
    thirds = np.zeros((S, 12), dtype=np.int16)
    ranks_count = np.zeros((48, 4))               # P(finish position)
    exp_pts = np.zeros(48)

    for gi, g in enumerate(GROUPS):
        pts = np.zeros((S, 4)); gd = np.zeros((S, 4)); gf = np.zeros((S, 4))
        for (k, x, y) in gmatch[g]:
            h, a = HS[:, k], AS[:, k]
            hw = (h > a); dr = (h == a)
            pts[:, x] += 3 * hw + dr
            pts[:, y] += 3 * (~hw & ~dr) + dr
            gd[:, x] += h - a; gd[:, y] += a - h
            gf[:, x] += h; gf[:, y] += a
        u = rng.random((S, 4))
        key = pts * 1e7 + (gd + 100) * 1e4 + gf * 10 + u
        order = np.argsort(-key, axis=1)          # local indices, best first

        # two-way head-to-head correction on adjacent pairs tied on pts/gd/gf
        res = {}                                   # (x,y) -> sign per sim (+1 x beat y)
        for (k, x, y) in gmatch[g]:
            s = np.sign(HS[:, k].astype(np.int16) - AS[:, k].astype(np.int16))
            res[(x, y)] = s; res[(y, x)] = -s
        for _ in range(2):
            for pos in (0, 1, 2):
                a_ = order[:, pos]; b_ = order[:, pos + 1]
                rows = np.arange(S)
                tied = ((pts[rows, a_] == pts[rows, b_]) &
                        (gd[rows, a_] == gd[rows, b_]) &
                        (gf[rows, a_] == gf[rows, b_]))
                h2h = np.zeros(S)
                for (x, y), s in res.items():
                    m = (a_ == x) & (b_ == y)
                    if m.any():
                        h2h[m] = s[m]
                swap = tied & (h2h < 0)            # lower-ranked won the h2h
                if swap.any():
                    order[swap, pos], order[swap, pos + 1] = b_[swap], a_[swap]

        gteams = np.array([tidx[t] for t in groups[g]])
        winners[:, gi] = gteams[order[:, 0]]
        runners[:, gi] = gteams[order[:, 1]]
        thirds[:, gi] = gteams[order[:, 2]]
        for pos in range(4):
            np.add.at(ranks_count, gteams[order[:, pos]], np.eye(4)[pos])
        for loc in range(4):
            exp_pts[gteams[loc]] += pts[:, loc].sum() / S
        # stash thirds' records for cross-group ranking
        if gi == 0:
            tp = np.zeros((S, 12)); tgd = np.zeros((S, 12)); tgf = np.zeros((S, 12))
            main.third_stats = (tp, tgd, tgf)
        tp, tgd, tgf = main.third_stats
        rows = np.arange(S)
        tp[:, gi] = pts[rows, order[:, 2]]
        tgd[:, gi] = gd[rows, order[:, 2]]
        tgf[:, gi] = gf[rows, order[:, 2]]

    # ---------------- best eight thirds + Annex C ----------------
    tp, tgd, tgf = main.third_stats
    tkey = tp * 1e7 + (tgd + 100) * 1e4 + tgf * 10 + rng.random((S, 12))
    third_rank = np.argsort(-tkey, axis=1)
    qual = np.zeros((S, 12), dtype=bool)
    np.put_along_axis(qual, third_rank[:, :8], True, axis=1)
    bitmask = (qual @ (1 << np.arange(12))).astype(np.int32)

    ac = pd.read_csv("data/annex_c.csv")
    slots = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]
    A = np.full((4096, 8), -1, dtype=np.int8)
    for _, r in ac.iterrows():
        bm = sum(1 << (ord(c) - 65) for c in r["combo"])
        A[bm] = [ord(r[s]) - 65 for s in slots]
    assign = A[bitmask]                            # (S, 8) group index of third per slot
    assert (assign >= 0).all(), "unmapped third-place combination"
    rows = np.arange(S)
    third_team_for_slot = {slots[k]: thirds[rows, assign[:, k]] for k in range(8)}

    # ---------------- knockout bracket ----------------
    P0, P1 = ko_win_tables(teams, dc, eg, ratings, w)

    def play(th, ta, venue):
        cth = host_country[th] == venue
        cta = host_country[ta] == venue
        p = np.where(cth, P1[th, ta], np.where(cta, 1.0 - P1[ta, th], P0[th, ta]))
        return np.where(rng.random(len(th)) < p, th, ta)

    reached = {st: np.zeros(48) for st in
               ["r32", "r16", "qf", "sf", "final", "champion"]}

    def mark(stage, *arrs):
        for a in arrs:
            np.add.at(reached[stage], a, 1.0)

    gidx = {c: i for i, c in enumerate(GROUPS)}
    wmatch = {}
    for mno, info in tj["round_of_32"].items():
        def teams_of(code, info=info, mno=mno):
            if code == "3rd":
                return third_team_for_slot[info["third_slot"]]
            kind, g = code[0], code[1]
            return winners[:, gidx[g]] if kind == "1" else runners[:, gidx[g]]
        th = teams_of(info["home"]); ta = teams_of(info["away"])
        mark("r32", th, ta)
        wmatch[mno] = play(th, ta, info["venue_country"])

    for rnd, stage in (("round_of_16", "r16"), ("quarterfinals", "qf"),
                       ("semifinals", "sf"), ("final", "final")):
        for mno, (m1, m2, venue) in tj[rnd].items():
            th, ta = wmatch[m1], wmatch[m2]
            mark(stage, th, ta)
            wmatch[mno] = play(th, ta, venue)
    champ = wmatch["104"]
    mark("champion", champ)

    # ---------------- aggregate & save ----------------
    out = pd.DataFrame({
        "team": teams,
        "group": [group_of[t] for t in teams],
        "elo": [ratings.get(t, 1500.0) for t in teams],
        "dc_attack": [dc.attack[dc.index[t]] for t in teams],
        "dc_defence": [dc.defence[dc.index[t]] for t in teams],
        "exp_group_points": exp_pts,
        "p_win_group": ranks_count[:, 0] / S,
        "p_group_2nd": ranks_count[:, 1] / S,
        "p_group_3rd": ranks_count[:, 2] / S,
        "p_group_4th": ranks_count[:, 3] / S,
        "p_reach_r32": reached["r32"] / S,
        "p_reach_r16": reached["r16"] / S,
        "p_reach_qf": reached["qf"] / S,
        "p_reach_sf": reached["sf"] / S,
        "p_reach_final": reached["final"] / S,
        "p_champion": reached["champion"] / S,
    }).sort_values("p_champion", ascending=False)
    out.to_csv("output/team_probabilities.csv", index=False)

    # most common finals
    f_th, f_ta = wmatch["101"], wmatch["102"]
    pairs = np.minimum(f_th, f_ta) * 48 + np.maximum(f_th, f_ta)
    vc = pd.Series(pairs).value_counts().head(10)
    finals = [{"final": f"{teams[p // 48]} vs {teams[p % 48]}", "p": c / S}
              for p, c in vc.items()]

    summary = {
        "n_sims": S, "seed": SEED, "cutoff": str(CUTOFF.date()),
        "blend_w": w, "dc_home_adv": dc.home_adv, "dc_rho": dc.rho,
        "top_finals": finals,
        "champion_top10": out.head(10)[["team", "p_champion"]].to_dict("records"),
    }
    with open("output/sim_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary["champion_top10"], indent=None), flush=True)
    print("saved output/team_probabilities.csv, match_predictions.csv, sim_summary.json", flush=True)


if __name__ == "__main__":
    main()
