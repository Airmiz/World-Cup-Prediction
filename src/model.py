"""
World Cup 2026 prediction model.

Components
----------
1. World Football Elo ratings (eloratings.net algorithm) computed from the full
   1872-2026 international match history, with pre-match ratings stored for
   leakage-free downstream fits.
2. Time-decayed Dixon-Coles model: bivariate Poisson with attack/defence
   strengths per team, home advantage, low-score dependence correction (rho),
   exponential time decay and match-importance weights. Fitted by penalised
   maximum likelihood (Gaussian prior on team strengths = MAP / ridge).
3. Elo->goals bridge: weighted Poisson GLMs mapping (pre-match) Elo difference
   to home/away scoring rates.
4. Log-linear blend of (2) and (3); blend weight tuned out-of-sample.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from scipy.optimize import minimize, minimize_scalar

# ----------------------------------------------------------------------------
# Data loading and match importance
# ----------------------------------------------------------------------------

def k_factor(tournament: str) -> float:
    """Elo K-factor by competition importance (World Football Elo convention)."""
    t = tournament.lower()
    if t == "friendly":
        return 20.0
    if "qualification" in t:
        return 40.0
    if "world cup" in t:                      # WC finals
        return 60.0
    majors = ["uefa euro", "copa américa", "copa america", "african cup",
              "africa cup", "afc asian cup", "concacaf championship",
              "gold cup", "oceania nations cup", "confederations cup"]
    if any(m in t for m in majors):           # continental finals
        return 50.0
    if "nations league" in t:
        return 40.0
    return 30.0


def importance_weight(tournament: str, friendly_w: float) -> float:
    """Likelihood weight of a match in the Dixon-Coles / GLM fits."""
    k = k_factor(tournament)
    if k >= 50.0:
        return 1.0
    if k >= 40.0:
        return 0.85
    if k >= 30.0:
        return 0.7
    return friendly_w


def load_results(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ----------------------------------------------------------------------------
# Elo ratings
# ----------------------------------------------------------------------------

HOME_ELO_BONUS = 100.0

def run_elo(df: pd.DataFrame) -> tuple[dict[str, float], np.ndarray, np.ndarray]:
    """Chronological Elo pass over played matches.

    Returns (final_ratings, pre_match_elo_home, pre_match_elo_away) where the
    arrays align with df rows (NaN where a score is missing).
    """
    played = df["home_score"].notna().values
    ratings: dict[str, float] = {}
    n = len(df)
    eh = np.full(n, np.nan)
    ea = np.full(n, np.nan)
    ht = df["home_team"].values
    at = df["away_team"].values
    hs = df["home_score"].values
    as_ = df["away_score"].values
    neutral = df["neutral"].astype(str).str.upper().eq("TRUE").values
    ks = df["tournament"].map(k_factor).values

    for i in range(n):
        h, a = ht[i], at[i]
        rh = ratings.get(h, 1500.0)
        ra = ratings.get(a, 1500.0)
        eh[i], ea[i] = rh, ra
        if not played[i]:
            continue
        dr = rh - ra + (0.0 if neutral[i] else HOME_ELO_BONUS)
        we = 1.0 / (1.0 + 10.0 ** (-dr / 400.0))
        gd = abs(hs[i] - as_[i])
        g = 1.0 if gd <= 1 else (1.5 if gd == 2 else (11.0 + gd) / 8.0)
        w = 1.0 if hs[i] > as_[i] else (0.5 if hs[i] == as_[i] else 0.0)
        delta = ks[i] * g * (w - we)
        ratings[h] = rh + delta
        ratings[a] = ra - delta
    return ratings, eh, ea


# ----------------------------------------------------------------------------
# Dixon-Coles model
# ----------------------------------------------------------------------------

@dataclass
class DCParams:
    teams: list[str]
    attack: np.ndarray
    defence: np.ndarray
    mu: float
    home_adv: float
    rho: float
    index: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.index = {t: i for i, t in enumerate(self.teams)}

    def lambdas(self, home: str, away: str, home_advantage: bool) -> tuple[float, float]:
        i, j = self.index[home], self.index[away]
        ha = self.home_adv if home_advantage else 0.0
        lh = np.exp(self.mu + self.attack[i] - self.defence[j] + ha)
        la = np.exp(self.mu + self.attack[j] - self.defence[i])
        return lh, la


def fit_dixon_coles(df: pd.DataFrame, cutoff: pd.Timestamp, window_years: float = 12.0,
                    xi: float = 0.7, friendly_w: float = 0.5, ridge: float = 1.0) -> DCParams:
    """Weighted MAP fit of the Dixon-Coles model on matches before `cutoff`."""
    lo = cutoff - pd.Timedelta(days=int(window_years * 365.25))
    m = df[(df["date"] < cutoff) & (df["date"] >= lo) & df["home_score"].notna()].copy()
    teams = sorted(set(m["home_team"]) | set(m["away_team"]))
    T = len(teams)
    idx = {t: i for i, t in enumerate(teams)}
    hi = m["home_team"].map(idx).values
    ai = m["away_team"].map(idx).values
    hg = m["home_score"].values.astype(float)
    ag = m["away_score"].values.astype(float)
    nonneutral = ~m["neutral"].astype(str).str.upper().eq("TRUE").values
    dt_years = (cutoff - m["date"]).dt.days.values / 365.25
    w = np.exp(-xi * dt_years) * np.array(
        [importance_weight(t, friendly_w) for t in m["tournament"]])

    def unpack(theta):
        att = theta[:T] - theta[:T].mean()
        dfc = theta[T:2 * T] - theta[T:2 * T].mean()
        mu, ha = theta[2 * T], theta[2 * T + 1]
        return att, dfc, mu, ha

    def nll_grad(theta):
        att, dfc, mu, ha = unpack(theta)
        log_lh = mu + att[hi] - dfc[ai] + ha * nonneutral
        log_la = mu + att[ai] - dfc[hi]
        lh, la = np.exp(log_lh), np.exp(log_la)
        nll = -np.sum(w * (hg * log_lh - lh + ag * log_la - la))
        gh = w * (hg - lh)      # d logL / d log_lh
        ga = w * (ag - la)
        g_att = np.zeros(T); g_def = np.zeros(T)
        np.add.at(g_att, hi, gh); np.add.at(g_att, ai, ga)
        np.add.at(g_def, ai, -gh); np.add.at(g_def, hi, -ga)
        g_mu = gh.sum() + ga.sum()
        g_ha = (gh * nonneutral).sum()
        grad = -np.concatenate([g_att, g_def, [g_mu], [g_ha]])
        # ridge (Gaussian prior) on team strengths
        nll += ridge * (att @ att + dfc @ dfc)
        grad[:T] += 2 * ridge * att
        grad[T:2 * T] += 2 * ridge * dfc
        return nll, grad

    theta0 = np.zeros(2 * T + 2)
    theta0[2 * T] = np.log(max(hg.mean(), 0.1))
    res = minimize(nll_grad, theta0, jac=True, method="L-BFGS-B",
                   options={"maxiter": 500})
    att, dfc, mu, ha = unpack(res.x)

    # Stage 2: profile likelihood for rho on low-score dependence
    lh = np.exp(mu + att[hi] - dfc[ai] + ha * nonneutral)
    la = np.exp(mu + att[ai] - dfc[hi])

    def tau_ll(rho):
        t = np.ones_like(lh)
        m00 = (hg == 0) & (ag == 0); t[m00] = 1 - lh[m00] * la[m00] * rho
        m01 = (hg == 0) & (ag == 1); t[m01] = 1 + lh[m01] * rho
        m10 = (hg == 1) & (ag == 0); t[m10] = 1 + la[m10] * rho
        m11 = (hg == 1) & (ag == 1); t[m11] = 1 - rho
        if np.any(t <= 1e-10):
            return 1e12
        return -np.sum(w * np.log(t))

    r = minimize_scalar(tau_ll, bounds=(-0.2, 0.2), method="bounded")
    return DCParams(teams, att, dfc, float(mu), float(ha), float(r.x))


# ----------------------------------------------------------------------------
# Elo -> goals GLM
# ----------------------------------------------------------------------------

@dataclass
class EloGoals:
    a_h: float; b_h: float; a_a: float; b_a: float

    def lambdas(self, elo_home: float, elo_away: float, home_advantage: bool) -> tuple[float, float]:
        d = (elo_home - elo_away + (HOME_ELO_BONUS if home_advantage else 0.0)) / 400.0
        return np.exp(self.a_h + self.b_h * d), np.exp(self.a_a - self.b_a * d)


def fit_elo_goals(df: pd.DataFrame, eh: np.ndarray, ea: np.ndarray,
                  cutoff: pd.Timestamp, window_years: float = 12.0,
                  xi: float = 0.7, friendly_w: float = 0.5) -> EloGoals:
    lo = cutoff - pd.Timedelta(days=int(window_years * 365.25))
    sel = (df["date"] < cutoff) & (df["date"] >= lo) & df["home_score"].notna() & ~np.isnan(eh)
    m = df[sel]
    nonneutral = ~m["neutral"].astype(str).str.upper().eq("TRUE").values
    d = (eh[sel.values] - ea[sel.values] + HOME_ELO_BONUS * nonneutral) / 400.0
    dt_years = (cutoff - m["date"]).dt.days.values / 365.25
    w = np.exp(-xi * dt_years) * np.array(
        [importance_weight(t, friendly_w) for t in m["tournament"]])

    def fit_one(y, x):
        def nll_grad(p):
            a, b = p
            lam = np.exp(a + b * x)
            nll = -np.sum(w * (y * (a + b * x) - lam))
            r = w * (y - lam)
            return nll, -np.array([r.sum(), (r * x).sum()])
        return minimize(nll_grad, np.array([0.0, 0.0]), jac=True, method="L-BFGS-B").x

    a_h, b_h = fit_one(m["home_score"].values.astype(float), d)
    a_a, b_a = fit_one(m["away_score"].values.astype(float), -d)
    return EloGoals(float(a_h), float(b_h), float(a_a), float(b_a))


# ----------------------------------------------------------------------------
# Blend + score matrix
# ----------------------------------------------------------------------------

MAX_G = 12  # goals grid 0..12

def blend_lambdas(ldc: tuple[float, float], lel: tuple[float, float], w: float) -> tuple[float, float]:
    """Log-linear pool of the two goal-rate forecasts."""
    lh = np.exp(w * np.log(max(ldc[0], 1e-3)) + (1 - w) * np.log(max(lel[0], 1e-3)))
    la = np.exp(w * np.log(max(ldc[1], 1e-3)) + (1 - w) * np.log(max(lel[1], 1e-3)))
    return float(lh), float(la)


def score_matrix(lh: float, la: float, rho: float, max_g: int = MAX_G) -> np.ndarray:
    """Joint score PMF with Dixon-Coles low-score correction, renormalised."""
    g = np.arange(max_g + 1)
    from scipy.stats import poisson
    ph = poisson.pmf(g, lh)
    pa = poisson.pmf(g, la)
    P = np.outer(ph, pa)
    P[0, 0] *= max(1 - lh * la * rho, 1e-12)
    P[0, 1] *= 1 + lh * rho
    P[1, 0] *= 1 + la * rho
    P[1, 1] *= 1 - rho
    return P / P.sum()


def outcome_probs(P: np.ndarray) -> tuple[float, float, float]:
    return (float(np.tril(P, -1).sum()),   # home win
            float(np.trace(P)),            # draw
            float(np.triu(P, 1).sum()))    # away win
