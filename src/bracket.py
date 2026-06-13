"""Derive the model's single most-likely ("modal") bracket for display.

Group positions are filled by maximising per-slot finish probabilities from the
simulation; the eight qualifying thirds are the predicted third-placed teams
with the highest conditional qualification probability; their round-of-32
slots follow FIFA Annex C; each knockout tie advances the team the model
favours (probability shown), with venue-specific host advantage.
"""
import json
import pandas as pd

from simulate import build_model, pair_lambdas
from model import score_matrix, outcome_probs


def ko_prob(dc, eg, ratings, w, t1, t2, venue):
    """P(t1 beats t2 incl. extra time + penalties) at a given venue country."""
    hosts = ("United States", "Mexico", "Canada")
    if t1 in hosts and t1 == venue:
        home, away, flip = t1, t2, False,
    elif t2 in hosts and t2 == venue:
        home, away, flip = t2, t1, True
    else:
        home, away, flip = t1, t2, False
    adv = home in hosts and home == venue
    lh, la = pair_lambdas(dc, eg, ratings, w, home, away, adv)
    p90h, p90d, _ = outcome_probs(score_matrix(lh, la, dc.rho))
    peth, petd, _ = outcome_probs(score_matrix(lh / 3, la / 3, dc.rho))
    ph = p90h + p90d * (peth + petd * 0.5)
    return (1 - ph) if flip else ph


def main():
    df, ratings, dc, eg, w = build_model()
    tp = pd.read_csv("output/team_probabilities.csv")
    tj = json.load(open("data/tournament.json"))
    ac = pd.read_csv("data/annex_c.csv")

    # ---- modal group standings ----
    standings = {}
    for g in "ABCDEFGHIJKL":
        sub = tp[tp["group"] == g].set_index("team")
        rest = list(sub.index)
        first = sub.loc[rest, "p_win_group"].idxmax(); rest.remove(first)
        second = sub.loc[rest, "p_group_2nd"].idxmax(); rest.remove(second)
        third = sub.loc[rest, "p_group_3rd"].idxmax(); rest.remove(third)
        standings[g] = {"1": first, "2": second, "3": third, "4": rest[0],
                        "probs": {"1": float(sub.loc[first, "p_win_group"]),
                                  "2": float(sub.loc[second, "p_group_2nd"]),
                                  "3": float(sub.loc[third, "p_group_3rd"])}}

    # ---- best eight thirds (conditional qualification odds) ----
    q3 = {}
    for g, s in standings.items():
        r = tp[tp["team"] == s["3"]].iloc[0]
        cond = (r["p_reach_r32"] - r["p_win_group"] - r["p_group_2nd"]) / max(r["p_group_3rd"], 1e-9)
        q3[g] = min(cond, 1.0)
    qual_groups = sorted(sorted(q3, key=q3.get, reverse=True)[:8])
    combo = "".join(qual_groups)
    row = ac[ac["combo"] == combo].iloc[0]
    third_for_slot = {s: standings[row[s]]["3"] for s in
                      ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]}

    # ---- knockout walk ----
    matches = {}
    def team_of(code, info):
        if code == "3rd":
            return third_for_slot[info["third_slot"]]
        return standings[code[1]][code[0]]

    bracket = {"standings": standings, "qualified_third_groups": qual_groups,
               "third_slotting": third_for_slot, "rounds": {}}
    r32 = {}
    for mno, info in tj["round_of_32"].items():
        t1, t2 = team_of(info["home"], info), team_of(info["away"], info)
        p = ko_prob(dc, eg, ratings, w, t1, t2, info["venue_country"])
        winner = t1 if p >= 0.5 else t2
        r32[mno] = winner
        matches[mno] = {"m": int(mno), "t1": t1, "t2": t2,
                        "p1": round(p, 4), "winner": winner,
                        "venue": info["venue_country"],
                        "label": f"{info['home']} v {info['away']}"}
    bracket["rounds"]["r32"] = [matches[k] for k in sorted(r32, key=int)]

    prev = r32
    for rnd, key in (("round_of_16", "r16"), ("quarterfinals", "qf"),
                     ("semifinals", "sf"), ("final", "final")):
        cur = {}
        out = []
        for mno, (m1, m2, venue) in tj[rnd].items():
            t1, t2 = prev[m1], prev[m2]
            p = ko_prob(dc, eg, ratings, w, t1, t2, venue)
            winner = t1 if p >= 0.5 else t2
            cur[mno] = winner
            out.append({"m": int(mno), "t1": t1, "t2": t2, "p1": round(p, 4),
                        "winner": winner, "venue": venue})
        bracket["rounds"][key] = sorted(out, key=lambda x: x["m"])
        prev = {**prev, **cur}

    bracket["champion"] = bracket["rounds"]["final"][0]["winner"]
    json.dump(bracket, open("output/bracket.json", "w"), indent=1)
    print("champion:", bracket["champion"])
    print("final:", bracket["rounds"]["final"][0])
    print("thirds combo:", combo)


if __name__ == "__main__":
    main()
