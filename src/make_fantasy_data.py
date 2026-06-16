"""Build the Fantasy player database -> data/fantasy.json for the Fantasy page.

Squads: openfootball (open data, same source as our goal minutes).
Points: a real FPL-style engine scores every player for every match already played,
from the live ESPN data we store (minutes, goals by position, assists, clean sheets,
saves, goals conceded, cards, own goals, + match bonus). Points are bucketed into
gameweeks (group matchdays 1-3, then the knockout rounds) and embedded per player, so
the page is one source of truth and just sums them for the user's squad.
Price = team strength (model) + position + first-choice/starts + form (points so far),
clamped 4.0-13.0, so prices spread wide and evolve through the tournament.
"""
from __future__ import annotations
import json, os, urllib.request, csv, unicodedata, datetime

SQUADS_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.squads.json"
SQPOS = {"GK": "GK", "DF": "DEF", "MF": "MID", "FW": "FWD"}      # openfootball squad pos
EVPOS = {"G": "GK", "D": "DEF", "M": "MID", "F": "FWD"}          # lineup event pos bucket
ALIAS = {"Korea Republic": "South Korea", "IR Iran": "Iran", "USA": "United States",
         "Côte d'Ivoire": "Ivory Coast", "Cote d'Ivoire": "Ivory Coast", "Czechia": "Czech Republic",
         "Turkiye": "Turkey", "Türkiye": "Turkey", "Cape Verde Islands": "Cape Verde",
         "Congo DR": "DR Congo", "Bosnia-Herzegovina": "Bosnia and Herzegovina"}
GOAL = {"GK": 6, "DEF": 6, "MID": 5, "FWD": 4}
CS = {"GK": 4, "DEF": 4, "MID": 1, "FWD": 0}


def jget(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40) as r:
        return json.load(r)

def norm(n):
    return unicodedata.normalize("NFKD", (n or "")).encode("ascii", "ignore").decode().lower().strip()

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(c if c.isalnum() else "-" for c in s).strip("-")


def match_points(L, home, away):
    """Per-player fantasy points for one finished/played match record L."""
    ev = L.get("events") or []
    side_team = {"home": home, "away": away}
    hg = sum(1 for e in ev if e.get("type") == "goal" and e.get("team") == "home")
    ag = sum(1 for e in ev if e.get("type") == "goal" and e.get("team") == "away")
    conceded = {"home": ag, "away": hg}
    onMin, offMin = {}, {}
    for e in ev:
        if e.get("type") == "subst":
            if e.get("assist"):
                onMin[norm(e["assist"])] = e.get("min", 60)
            if e.get("player"):
                offMin[norm(e["player"])] = e.get("min", 60)
    rows = []
    for side in ("home", "away"):
        b = L.get(side) or {}
        starters = {norm(p.get("name")) for p in (b.get("xi") or [])}
        for p in (b.get("xi") or []) + (b.get("subs") or []):
            nm = norm(p.get("name"))
            started = nm in starters
            came_on = nm in onMin
            if not started and not came_on:
                continue
            pos = EVPOS.get((p.get("pos") or "M")[:1].upper(), "MID")
            mins = offMin.get(nm, 90) if started else (90 - onMin.get(nm, 90))
            pts = 2 if mins >= 60 else 1
            g = a = og = 0
            for e in ev:
                if e.get("type") != "goal":
                    continue
                d = (e.get("detail") or "").lower()
                if norm(e.get("assist") or "") == nm:
                    a += 1
                if norm(e.get("player") or "") == nm:
                    if "own" in d:
                        og += 1
                    elif "miss" not in d:
                        g += 1
            pts += g * GOAL[pos] + a * 3 - og * 2
            for e in ev:
                if e.get("type") == "card" and norm(e.get("player") or "") == nm:
                    pts += -3 if e.get("card") == "red" else -1
            st = p.get("st") or {}
            if pos in ("GK", "DEF") and started and mins >= 60 and conceded[side] == 0:
                pts += CS[pos]
            if pos == "GK":
                try:
                    pts += int(float(st.get("SV", 0) or 0)) // 3
                except (TypeError, ValueError):
                    pass
                pts += -(conceded[side] // 2)
            elif pos == "DEF":
                pts += -(conceded[side] // 2)
            rows.append([side_team[side], p.get("name"), pos, pts, g, a])
    # match bonus: top 3 by points get +3/+2/+1
    order = sorted(range(len(rows)), key=lambda i: -rows[i][3])
    for rank, i in enumerate(order[:3]):
        rows[i][3] += (3, 2, 1)[rank]
    return rows  # [team, name, pos, points, goals, assists]


def main():
    squads = jget(SQUADS_URL)

    strength = {}
    if os.path.exists("output/team_probabilities.csv"):
        for r in csv.DictReader(open("output/team_probabilities.csv")):
            strength[r["team"]] = {"elo": float(r["elo"]), "att": float(r["dc_attack"]), "def": float(r["dc_defence"])}
    def pct(vals):
        lo, hi = min(vals), max(vals); rng = (hi - lo) or 1
        return lambda x: (x - lo) / rng
    elo_p = pct([s["elo"] for s in strength.values()]) if strength else (lambda x: .5)
    att_p = pct([s["att"] for s in strength.values()]) if strength else (lambda x: .5)
    def_p = pct([s["def"] for s in strength.values()]) if strength else (lambda x: .5)

    # gameweek of each group fixture: within a group, fixtures sorted by date -> MD 1/2/3
    gw_of = {}
    if os.path.exists("output/match_predictions.csv"):
        rows = list(csv.DictReader(open("output/match_predictions.csv")))
        bygrp = {}
        for r in rows:
            bygrp.setdefault(r["group"], []).append(r)
        for g, fx in bygrp.items():
            fx.sort(key=lambda r: r["date"])
            for i, r in enumerate(fx):
                gw_of[r["home_team"] + "|" + r["away_team"]] = i // 2 + 1   # 2 matches per matchday

    # build player index + score played matches
    players, idx = [], {}    # idx[(team, normname)] = player dict
    for s in squads:
        tname = ALIAS.get(s["name"], s["name"])
        for p in s.get("players", []):
            pl = {"id": slug(tname) + "-" + slug(p["name"]), "name": p["name"], "team": tname,
                  "group": s.get("group", ""), "pos": SQPOS.get(p.get("pos"), "MID"),
                  "num": p.get("number"), "gw": {}, "pts": 0, "g": 0, "a": 0, "starts": 0, "apps": 0}
            players.append(pl); idx[(tname, norm(p["name"]))] = pl

    matched = unmatched = 0
    if os.path.exists("data/lineups.json"):
        for key, L in json.load(open("data/lineups.json")).items():
            if not isinstance(L, dict) or "|" not in key:
                continue
            home, away = key.split("|", 1)
            gw = gw_of.get(key, 0)
            for team, name, pos, pts, g, a in match_points(L, home, away):
                pl = idx.get((team, norm(name)))
                if not pl:
                    unmatched += 1; continue
                matched += 1
                pl["gw"][str(gw)] = pl["gw"].get(str(gw), 0) + pts
                pl["pts"] += pts; pl["g"] += g; pl["a"] += a; pl["apps"] += 1
            # starts (for pricing)
            for side, team in (("home", home), ("away", away)):
                for p in ((L.get(side) or {}).get("xi") or []):
                    pl = idx.get((team, norm(p.get("name"))))
                    if pl:
                        pl["starts"] += 1

    POSBASE = {"GK": 4.0, "DEF": 4.0, "MID": 4.5, "FWD": 5.0}
    TEAMSLOPE = {"GK": 3.0, "DEF": 3.5, "MID": 4.5, "FWD": 5.5}
    for pl in players:
        st = strength.get(pl["team"])
        if st:
            ts = (0.5 * elo_p(st["elo"]) + 0.5 * att_p(st["att"])) if pl["pos"] in ("MID", "FWD") \
                else (0.5 * elo_p(st["elo"]) + 0.5 * def_p(st["def"]))
        else:
            ts = 0.45
        price = POSBASE[pl["pos"]] + TEAMSLOPE[pl["pos"]] * ts
        price += 0.5 * min(pl["starts"], 3)              # first-choice bump
        price += 0.13 * min(pl["pts"], 30)               # form (points so far)
        pl["price"] = max(4.0, min(13.0, round(price * 2) / 2))

    scoring = {"play60": 2, "play1": 1, "goal": GOAL, "assist": 3, "cs": CS,
               "save3": 1, "concede2": -1, "yellow": -1, "red": -3, "owngoal": -2, "bonus": [3, 2, 1]}
    out = {"generated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
           "budget": 100.0, "squad": {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3},
           "max_per_team": 3, "scoring": scoring,
           "gameweeks": [{"gw": i, "name": f"Matchday {i}"} for i in (1, 2, 3)],
           "players": players}
    json.dump(out, open("data/fantasy.json", "w"))
    pr = sorted(players, key=lambda x: -x["price"])
    print(f"[fantasy] {len(players)} players; event names matched {matched}, unmatched {unmatched}")
    print("  priciest:", ", ".join(f"{p['name']}({p['team'][:3]},{p['pos']},£{p['price']},{p['pts']}pt)" for p in pr[:8]))
    topsc = sorted(players, key=lambda x: -x["pts"])[:6]
    print("  top scorers:", ", ".join(f"{p['name']}({p['pts']}pt,{p['g']}g,£{p['price']})" for p in topsc))


if __name__ == "__main__":
    main()
