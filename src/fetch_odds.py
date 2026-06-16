"""Fetch pre-match betting-market odds for upcoming World Cup fixtures from ESPN.

The market (closing line) is the hardest benchmark to beat in football forecasting
(Egidi, Pauli & Torelli 2018; market-efficiency literature). We capture it here so
the model can be convex-blended toward it — the one peer-reviewed route to
bookmaker-grade accuracy. Writes data/odds_market.json keyed "home|away":
{h,d,a,prov} with the over-round removed. Cross-origin-safe, no key needed.
"""
from __future__ import annotations
import json, os, sys, urllib.request, datetime
import pandas as pd

ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
SCHED = "output/match_predictions.csv"
OUT = "data/odds_market.json"


def jget(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=25) as r:
            return json.load(r)
    except Exception:
        return {}


def ml_to_prob(ml):
    try:
        ml = float(ml)
    except (TypeError, ValueError):
        return None
    return 100.0 / (ml + 100.0) if ml > 0 else (-ml) / ((-ml) + 100.0)


def parse_market(summ):
    for o in (summ.get("pickcenter") or []):
        h = ml_to_prob((o.get("homeTeamOdds") or {}).get("moneyLine"))
        a = ml_to_prob((o.get("awayTeamOdds") or {}).get("moneyLine"))
        d = ml_to_prob((o.get("drawOdds") or {}).get("moneyLine"))
        if h is None or a is None:
            continue
        dd = d or 0.0
        tot = h + dd + a
        if tot <= 0:
            continue
        return {"h": round(h / tot, 4), "d": round(dd / tot, 4), "a": round(a / tot, 4),
                "prov": (o.get("provider") or {}).get("name") or "Market"}
    return None


def main():
    if not os.path.exists(SCHED):
        print("[odds] no schedule; skip"); return
    sched = pd.read_csv(SCHED)
    # canonical home/away pairs that are not yet played (no result in the schedule's date sense)
    pairs = {(r.home_team, r.away_team) for r in sched.itertuples()}
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}

    # scan a window from today forward for scheduled WC events
    today = datetime.date.today()
    lo = today.strftime("%Y%m%d"); hi = (today + datetime.timedelta(days=12)).strftime("%Y%m%d")
    sb = jget(f"{ESPN}/scoreboard?dates={lo}-{hi}")
    events = sb.get("events") or []
    fetched = 0
    for e in events:
        state = (((e.get("status") or {}).get("type") or {}).get("state"))
        if state != "pre":
            continue
        comp = (e.get("competitions") or [{}])[0]
        cs = comp.get("competitors") or []
        home = next((c["team"]["displayName"] for c in cs if c.get("homeAway") == "home"), None)
        away = next((c["team"]["displayName"] for c in cs if c.get("homeAway") == "away"), None)
        # ESPN uses its own home/away; match to our schedule either orientation
        key = None
        from_aliases = {"Czechia": "Czech Republic", "Türkiye": "Turkey", "Congo DR": "DR Congo",
                        "Bosnia-Herzegovina": "Bosnia and Herzegovina"}
        h2 = from_aliases.get(home, home); a2 = from_aliases.get(away, away)
        if (h2, a2) in pairs:
            key, flip = f"{h2}|{a2}", False
        elif (a2, h2) in pairs:
            key, flip = f"{a2}|{h2}", True
        if not key:
            continue
        s = jget(f"{ESPN}/summary?event={e['id']}")
        m = parse_market(s)
        if not m:
            continue
        if flip:  # our key orients home=first; swap h/a if ESPN had them reversed vs our schedule
            m = {"h": m["a"], "d": m["d"], "a": m["h"], "prov": m["prov"]}
        out[key] = m
        fetched += 1
    json.dump(out, open(OUT, "w"), indent=0)
    top = list(out.items())[-5:]
    print(f"[odds] {fetched} upcoming priced this run; {len(out)} total. e.g. " +
          "; ".join(f"{k} H{v['h']:.2f}/D{v['d']:.2f}/A{v['a']:.2f}" for k, v in top))


if __name__ == "__main__":
    main()
