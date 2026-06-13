"""Report figures from simulation + backtest artifacts."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})

tp = pd.read_csv("output/team_probabilities.csv")
bt = json.load(open("output/backtest.json"))

# --- fig 1: champion probabilities ---
top = tp.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.barh(top["team"], top["p_champion"] * 100, color="#1a6fb4")
for b, v in zip(bars, top["p_champion"] * 100):
    ax.text(b.get_width() + 0.15, b.get_y() + b.get_height() / 2, f"{v:.1f}%",
            va="center", fontsize=9)
ax.set_xlabel("Probability of winning the 2026 World Cup (%)")
ax.set_title("Champion probabilities — 200,000 tournament simulations", fontsize=12)
fig.tight_layout(); fig.savefig("output/fig_champion.png"); plt.close(fig)

# --- fig 2: calibration ---
cal = [c for c in bt["calibration"] if c["n"] > 0]
fig, ax = plt.subplots(figsize=(6, 6))
ax.plot([0, 1], [0, 1], "--", color="grey", lw=1, label="Perfect calibration")
x = [c["pred_mean"] for c in cal]; y = [c["obs_freq"] for c in cal]
n = [c["n"] for c in cal]
ax.scatter(x, y, s=[max(20, v) for v in n], color="#c0392b", zorder=3,
           label="Model (bin size ∝ matches)")
ax.set_xlabel("Predicted probability"); ax.set_ylabel("Observed frequency")
ax.set_title("Calibration — WC 2014/2018/2022 group stages\n(288 outcome probabilities)", fontsize=11)
ax.legend(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
fig.tight_layout(); fig.savefig("output/fig_calibration.png"); plt.close(fig)

# --- fig 3: advance-from-group probabilities ---
fig, ax = plt.subplots(figsize=(11, 7))
order = tp.sort_values(["group", "p_reach_r32"], ascending=[True, True])
ypos, labels, colors = [], [], []
y = 0
cmap = plt.get_cmap("tab20")
for gi, (g, sub) in enumerate(order.groupby("group")):
    for _, r in sub.iterrows():
        ypos.append(y); labels.append(f"{r['team']}  ({g})")
        colors.append(cmap(gi % 20))
        ax.barh(y, r["p_reach_r32"] * 100, color=cmap(gi % 20))
        y += 1
    y += 0.8
ax.set_yticks(ypos); ax.set_yticklabels(labels, fontsize=7)
ax.set_xlabel("Probability of reaching the round of 32 (%)")
ax.set_title("Advancement probability by group", fontsize=12)
ax.axvline(100 * 32 / 48, color="grey", ls=":", lw=1)
fig.tight_layout(); fig.savefig("output/fig_groups.png"); plt.close(fig)
print("figures saved")
