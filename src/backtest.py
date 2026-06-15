"""
Out-of-sample validation of the World Cup model.

Two layers of evidence:
  1. ROLLING-ORIGIN backtest over every competitive international since 2012
     (~9.5k matches) and over major-tournament finals only (~1.2k WC-like,
     balanced top-team matches). Components are refit monthly on data strictly
     before each refit date; pre-match Elo comes from a single chronological
     pass. This is the statistically powerful judge.
  2. The classic WC 2014 / 2018 / 2022 group-stage slices, kept for continuity.

Metrics: Rank Probability Score (RPS — the standard ordered-outcome football
metric), 3-way log loss and multiclass Brier, vs a uniform baseline and each
component alone.

Hyperparameters (time-decay xi, friendly weight, blend weight) are tuned on the
pre-2019 major-finals sample by RPS, subject to NOT regressing the WC group-stage
holdouts; 2019+ is the clean out-of-sample period. The selected configuration is
written to output/backtest.json and consumed by the production model.
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
MAJORS = ["FIFA World Cup", "UEFA Euro", "Copa América", "Copa America",
          "African Cup of Nations", "AFC Asian Cup", "Gold Cup",
          "CONCACAF Championship", "Confederations Cup"]
OOS_CUT = pd.Timestamp("2019-01-01")          # clean out-of-sample boundary


# ---------------------------------------------------------------- metrics
def rps3(p, y):
    cp = np.cumsum(p[:, :2], axis=1)
    co = np.cumsum(np.eye(3)[y][:, :2], axis=1)
    return float(np.mean(np.sum((cp - co) ** 2, axis=1) / 2.0))

def metrics(p, y):
    p = np.clip(np.asarray(p, float), 1e-12, 1); y = np.asarray(y)
    onehot = np.eye(3)[y]
    return {"n": int(len(y)),
            "log_loss": float(-np.mean(np.log(p[np.arange(len(y)), y]))),
            "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
            "rps": rps3(p, y)}

def uniform_metrics(y):
    p = np.full((len(y), 3), 1 / 3)
    return metrics(p, np.asarray(y))


# ---------------------------------------------------------------- fits cache
def month_starts(lo, hi):
    return list(pd.date_range(pd.Timestamp(lo), pd.Timestamp(hi), freq="MS"))

def build_fits(df, eh, ea, refits, xi, fw):
    return {t: (fit_dixon_coles(df, t, xi=xi, friendly_w=fw),
                fit_elo_goals(df, eh, ea, t, xi=xi, friendly_w=fw)) for t in refits}


# ---------------------------------------------------------------- rolling predict
def predict(df, eh, ea, idx, fits, w):
    refit = np.array(sorted(fits.keys()))
    H = df["home_team"].values; A = df["away_team"].values
    HS = df["home_score"].values; AS = df["away_score"].values
    NEU = df["neutral"].astype(str).str.upper().eq("TRUE").values
    DATE = df["date"].values
    P, Y, D = [], [], []
    for i in idx:
        k = np.searchsorted(refit, DATE[i], side="right") - 1
        if k < 0:
            continue
        dc, eg = fits[refit[k]]
        ha = not NEU[i]
        try:
            ldc = dc.lambdas(H[i], A[i], ha)
        except KeyError:
            continue
        rh = eh[i] if not np.isnan(eh[i]) else 1500.0
        ra = ea[i] if not np.isnan(ea[i]) else 1500.0
        lh, la = blend_lambdas(ldc, eg.lambdas(rh, ra, ha), w)
        pH, pD, pA = outcome_probs(score_matrix(lh, la, dc.rho))
        P.append([pH, pD, pA])
        Y.append(0 if HS[i] > AS[i] else (1 if HS[i] == AS[i] else 2))
        D.append(pd.Timestamp(DATE[i]))
    return np.array(P), np.array(Y), np.array(D)


# ---------------------------------------------------------------- index helpers
def wc_group_idx(df, year):
    s, e = WC[year]
    return np.where((df["tournament"] == "FIFA World Cup") & (df["date"] >= s)
                    & (df["date"] <= e) & df["home_score"].notna())[0]

def major_idx(df, start="2012-01-01", end="2026-06-11"):
    d = df["date"]
    return np.where((d >= start) & (d < end) & df["home_score"].notna()
                    & df["tournament"].isin(MAJORS))[0]

def broad_idx(df, start="2012-01-01", end="2026-06-11"):
    d = df["date"]
    return np.where((d >= start) & (d < end) & df["home_score"].notna()
                    & ~df["tournament"].str.lower().eq("friendly"))[0]


def main():
    df = load_results("data/results.csv")
    _, eh, ea = run_elo(df)
    refits = month_starts("2011-06-01", "2026-06-01")

    idx_major = major_idx(df); idx_broad = broad_idx(df)
    wc_idx = {y: wc_group_idx(df, y) for y in WC}

    # ---- tuning grid (fits depend only on xi, fw) ----
    grid_xi = [0.4, 0.5, 0.7]; grid_fw = [0.7]; grid_w = [0.4, 0.5, 0.6]
    INC = (0.7, 0.7, 0.5)                       # incumbent / production-to-date
    fits_by = {}
    for xi in grid_xi:
        for fw in grid_fw:
            fits_by[(xi, fw)] = build_fits(df, eh, ea, refits, xi, fw)
            print(f"fitted xi={xi} fw={fw}", flush=True)

    def majors_train_rps(fits, w):
        p, y, d = predict(df, eh, ea, idx_major, fits, w)
        m = d < OOS_CUT
        return metrics(p[m], y[m])["rps"]
    def wc_rps(fits, w, year):
        p, y, _ = predict(df, eh, ea, wc_idx[year], fits, w)
        return metrics(p, y)["rps"]

    inc_fits = fits_by[(INC[0], INC[1])]
    inc_wc = {y: wc_rps(inc_fits, INC[2], y) for y in (2014, 2018)}

    tuning = []
    for xi in grid_xi:
        for fw in grid_fw:
            for w in grid_w:
                f = fits_by[(xi, fw)]
                tr = majors_train_rps(f, w)
                w14, w18 = wc_rps(f, w, 2014), wc_rps(f, w, 2018)
                ok = (w14 <= inc_wc[2014] + 1e-3) and (w18 <= inc_wc[2018] + 1e-3)
                tuning.append({"xi": xi, "friendly_w": fw, "blend_w": w,
                               "train_majors_rps": tr, "wc2014_rps": w14,
                               "wc2018_rps": w18, "no_wc_regression": bool(ok)})
    # pick: best pre-2019 major-finals RPS that does not regress the WC holdouts
    feasible = [t for t in tuning if t["no_wc_regression"]]
    best_cfg = min(feasible, key=lambda t: t["train_majors_rps"])
    xi, fw, w = best_cfg["xi"], best_cfg["friendly_w"], best_cfg["blend_w"]
    print(f"SELECTED xi={xi} fw={fw} w={w} "
          f"(train majors RPS {best_cfg['train_majors_rps']:.4f})", flush=True)

    out = {"method": ("rolling-origin (monthly refit, leakage-free) over competitive "
                      "internationals since 2012; tuned on pre-2019 major finals by RPS "
                      "subject to no WC group-stage regression; 2019+ is out-of-sample"),
           "primary_metric": "rps",
           "best": {"xi": xi, "friendly_w": fw, "blend_w": w},
           "tuning_grid": tuning}

    # ---- classic WC group-stage blocks at the chosen config ----
    best_fits = fits_by[(xi, fw)]
    for y in WC:
        idx = wc_idx[y]
        pb, yb, _ = predict(df, eh, ea, idx, best_fits, w)
        pe, _, _ = predict(df, eh, ea, idx, best_fits, 0.0)
        pdc, _, _ = predict(df, eh, ea, idx, best_fits, 1.0)
        out[str(y)] = {"blend": metrics(pb, yb), "elo_only": metrics(pe, yb),
                       "dc_only": metrics(pdc, yb), "uniform": uniform_metrics(yb)}
        print(y, json.dumps(out[str(y)]["blend"]), flush=True)

    # ---- rolling out-of-sample validation: incumbent vs chosen ----
    def oos(fits, w, idx):
        p, y, d = predict(df, eh, ea, idx, fits, w)
        m = d >= OOS_CUT
        return metrics(p[m], y[m])
    out["validation_2019plus"] = {
        "major_finals": {"incumbent": oos(inc_fits, INC[2], idx_major),
                         "chosen": oos(best_fits, w, idx_major)},
        "all_competitive": {"incumbent": oos(inc_fits, INC[2], idx_broad),
                            "chosen": oos(best_fits, w, idx_broad)},
        "incumbent_config": {"xi": INC[0], "friendly_w": INC[1], "blend_w": INC[2]},
    }
    vm = out["validation_2019plus"]["major_finals"]
    print(f"OOS majors 2019+: incumbent rps={vm['incumbent']['rps']:.4f} "
          f"-> chosen rps={vm['chosen']['rps']:.4f}", flush=True)

    # ---- calibration (pooled WC group stages, chosen config) ----
    allp, ally = [], []
    for y in WC:
        pb, yb, _ = predict(df, eh, ea, wc_idx[y], best_fits, w)
        allp.append(pb); ally.append(yb)
    probs = np.vstack(allp).ravel()
    hits = np.eye(3)[np.concatenate(ally)].ravel()
    bins = np.linspace(0, 1, 11)
    bi = np.clip(np.digitize(probs, bins) - 1, 0, 9)
    out["calibration"] = [
        {"bin_mid": float((bins[i] + bins[i + 1]) / 2),
         "pred_mean": float(probs[bi == i].mean()) if np.any(bi == i) else None,
         "obs_freq": float(hits[bi == i].mean()) if np.any(bi == i) else None,
         "n": int((bi == i).sum())} for i in range(10)]

    with open("output/backtest.json", "w") as f:
        json.dump(out, f, indent=2)
    print("saved output/backtest.json", flush=True)


if __name__ == "__main__":
    main()
