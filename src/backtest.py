"""
Out-of-sample validation on the 2014, 2018 and 2022 World Cup group stages.

Protocol
--------
For each tournament, every component is fitted strictly on data available
before its first match (Elo through the prior day; Dixon-Coles and the
Elo-goals GLM on a trailing window). Hyperparameters (time-decay xi, friendly
weight, blend weight) are tuned on 2014+2018 jointly; 2022 is held out and
only ever scored with the tuned configuration. Metrics: 3-way log loss and
multiclass Brier score on 90-minute results, vs a uniform baseline and each
component alone.
"""
from __future__ import annotations

import json
import numpy as np
import pandas as pd
from model import (load_results, run_elo, fit_dixon_coles, fit_elo_goals,
                   blend_lambdas, score_matrix, outcome_probs)

WC = {
    2014: ("2014-06-12", "2014-06-26"),
    2018: ("2018-06-14", "2018-06-28"),
    2022: ("2022-11-20", "2022-12-02"),
}


def group_matches(df: pd.DataFrame, year: int) -> pd.DataFrame:
    start, gend = WC[year]
    return df[(df["tournament"] == "FIFA World Cup")
              & (df["date"] >= start) & (df["date"] <= gend)
              & df["home_score"].notna()]


def predict_with(dc, eg, ratings_at, matches: pd.DataFrame, blend_w: float, year: int) -> pd.DataFrame:
    rows = []
    for _, r in matches.iterrows():
        home_adv = str(r["neutral"]).upper() != "TRUE"
        ldc = dc.lambdas(r["home_team"], r["away_team"], home_adv)
        lel = eg.lambdas(ratings_at.get(r["home_team"], 1500.0),
                         ratings_at.get(r["away_team"], 1500.0), home_adv)
        lh, la = blend_lambdas(ldc, lel, blend_w)
        P = score_matrix(lh, la, dc.rho)
        pH, pD, pA = outcome_probs(P)
        out = 0 if r["home_score"] > r["away_score"] else (1 if r["home_score"] == r["away_score"] else 2)
        rows.append({"year": year, "home": r["home_team"], "away": r["away_team"],
                     "pH": pH, "pD": pD, "pA": pA, "outcome": out})
    return pd.DataFrame(rows)


def metrics(pred: pd.DataFrame) -> dict:
    p = pred[["pH", "pD", "pA"]].values
    y = pred["outcome"].values
    py = np.clip(p[np.arange(len(y)), y], 1e-12, 1)
    onehot = np.eye(3)[y]
    return {"n": int(len(y)),
            "log_loss": float(-np.mean(np.log(py))),
            "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1)))}


def main():
    df = load_results("data/results.csv")
    _, eh, ea = run_elo(df)

    # Elo snapshots strictly before each tournament
    snaps = {}
    for y in WC:
        sub = df[df["date"] < pd.Timestamp(WC[y][0])]
        snaps[y], _, _ = run_elo(sub)

    grid_xi = [0.35, 0.7, 1.1]
    grid_fw = [0.4, 0.7]
    grid_w = [0.0, 0.25, 0.5, 0.75, 1.0]

    # cache component fits per (xi, fw, year)
    fits = {}
    for xi in grid_xi:
        for fw in grid_fw:
            for y in WC:
                cutoff = pd.Timestamp(WC[y][0])
                dc = fit_dixon_coles(df, cutoff, xi=xi, friendly_w=fw)
                eg = fit_elo_goals(df, eh, ea, cutoff, xi=xi, friendly_w=fw)
                fits[(xi, fw, y)] = (dc, eg)
                print(f"fitted xi={xi} fw={fw} year={y} "
                      f"(home_adv={dc.home_adv:.3f}, rho={dc.rho:.3f})", flush=True)

    gm = {y: group_matches(df, y) for y in WC}

    results = []
    for xi in grid_xi:
        for fw in grid_fw:
            for w in grid_w:
                preds = [predict_with(*fits[(xi, fw, y)], snaps[y], gm[y], w, y)
                         for y in (2014, 2018)]
                mm = metrics(pd.concat(preds))
                results.append({"xi": xi, "fw": fw, "w": w, **mm})
    res = pd.DataFrame(results).sort_values("log_loss")
    best = res.iloc[0]
    xi, fw, w = float(best["xi"]), float(best["fw"]), float(best["w"])
    print("BEST on 2014+2018:", best.to_dict(), flush=True)

    out = {"tuning_grid": res.to_dict("records"),
           "best": {"xi": xi, "friendly_w": fw, "blend_w": w}}
    final_preds = []
    for y in (2014, 2018, 2022):
        dc, eg = fits[(xi, fw, y)]
        pb = predict_with(dc, eg, snaps[y], gm[y], w, y)
        pe = predict_with(dc, eg, snaps[y], gm[y], 0.0, y)
        pdc = predict_with(dc, eg, snaps[y], gm[y], 1.0, y)
        out[str(y)] = {"blend": metrics(pb), "elo_only": metrics(pe),
                       "dc_only": metrics(pdc),
                       "uniform": {"log_loss": float(-np.log(1 / 3)),
                                   "brier": float(2 / 3), "n": len(pb)}}
        final_preds.append(pb)
        print(y, json.dumps(out[str(y)]), flush=True)

    allp = pd.concat(final_preds)
    probs = allp[["pH", "pD", "pA"]].values.ravel()
    hits = np.eye(3)[allp["outcome"].values].ravel()
    bins = np.linspace(0, 1, 11)
    bi = np.clip(np.digitize(probs, bins) - 1, 0, 9)
    out["calibration"] = [
        {"bin_mid": float((bins[i] + bins[i + 1]) / 2),
         "pred_mean": float(probs[bi == i].mean()) if np.any(bi == i) else None,
         "obs_freq": float(hits[bi == i].mean()) if np.any(bi == i) else None,
         "n": int((bi == i).sum())} for i in range(10)]
    allp.to_csv("output/backtest_predictions.csv", index=False)
    with open("output/backtest.json", "w") as f:
        json.dump(out, f, indent=2)
    print("saved output/backtest.json", flush=True)


if __name__ == "__main__":
    main()
