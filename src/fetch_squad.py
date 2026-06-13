"""Fetch lineups, formations, cards and substitutions for WC2026 matches from
API-Football (https://www.api-sports.io/), whose free tier includes lineups and
events. Writes data/lineups.json keyed by "Home|Away". No-ops cleanly when the
API_FOOTBALL_KEY environment variable is absent, so the rest of the pipeline is
unaffected until a key is provided.

Standard library only. Usage: python3 src/fetch_squad.py
Set the key as a GitHub Actions secret named API_FOOTBALL_KEY.
"""
import csv
import json
import os
import sys
import time
import unicodedata
import urllib.request

API = "https://v3.football.api-sports.io"
LEAGUE = 1          # FIFA World Cup
SEASON = 2026
KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()

ALIASES = {
    "usa": "United States", "south korea": "South Korea", "korea republic": "South Korea",
    "ir iran": "Iran", "iran": "Iran", "turkiye": "Turkey", "czechia": "Czech Republic",
    "bosnia and herzegovina": "Bosnia and Herzegovina", "ivory coast": "Ivory Coast",
    "cote divoire": "Ivory Coast", "cape verde islands": "Cape Verde", "cape verde": "Cape Verde",
    "dr congo": "DR Congo", "congo dr": "DR Congo",
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    for ch in ".-&/'":
        s = s.replace(ch, " ")
    return " ".join(s.split())


def canon(name, fixture_names):
    n = norm(name)
    if n in ALIASES:
        return ALIASES[n]
    for fn in fixture_names:
        if norm(fn) == n:
            return fn
    return None


def api_get(path, params):
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    req = urllib.request.Request(f"{API}{path}?{qs}", headers={"x-apisports-key": KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def parse_lineup(team_block):
    return {
        "formation": team_block.get("formation") or "",
        "xi": [{"name": p["player"]["name"], "num": p["player"].get("number"),
                "pos": p["player"].get("pos")} for p in team_block.get("startXI", [])],
        "subs": [{"name": p["player"]["name"], "num": p["player"].get("number"),
                  "pos": p["player"].get("pos")} for p in team_block.get("substitutes", [])],
    }


def parse_events(events, home_name, away_name):
    out = []
    for e in events:
        side = "home" if (e.get("team", {}).get("name") == home_name) else "away"
        typ = (e.get("type") or "").lower()
        detail = (e.get("detail") or "")
        item = {"min": e.get("time", {}).get("elapsed") or 0, "team": side,
                "player": (e.get("player") or {}).get("name"), "type": typ, "detail": detail}
        if e.get("assist", {}).get("name"):
            item["assist"] = e["assist"]["name"]
        if typ == "card":
            item["card"] = "red" if "red" in detail.lower() else "yellow"
        out.append(item)
    return out


def main():
    if not KEY:
        print("[fetch_squad] API_FOOTBALL_KEY not set — skipping (lineups/cards/subs stay hidden).")
        return 0

    fixtures = []
    with open("data/results.csv") as f:
        for row in csv.DictReader(f):
            if row["tournament"] == "FIFA World Cup" and row["date"] >= "2026-06-01":
                fixtures.append((row["home_team"], row["away_team"]))
    fixture_names = sorted({t for p in fixtures for t in p})
    pair_set = {(h, a) for h, a in fixtures}

    path = "data/lineups.json"
    existing = json.load(open(path)) if os.path.exists(path) else {}

    try:
        payload = api_get("/fixtures", {"league": LEAGUE, "season": SEASON})
        fx = payload.get("response", [])
    except Exception as e:
        print(f"[fetch_squad] fixtures fetch failed: {e}")
        return 0

    # --- diagnostics: what did API-Football actually return? ---
    errs = payload.get("errors")
    print(f"[fetch_squad] /fixtures league={LEAGUE} season={SEASON}: results={payload.get('results')} errors={errs}")
    if fx:
        from collections import Counter
        st = Counter(x.get("fixture", {}).get("status", {}).get("short", "?") for x in fx)
        print(f"[fetch_squad] fixture statuses: {dict(st)}")
        sample = [f'{x["teams"]["home"]["name"]} v {x["teams"]["away"]["name"]} [{x.get("fixture",{}).get("status",{}).get("short")}]' for x in fx[:4]]
        print(f"[fetch_squad] sample fixtures: {sample}")
    else:
        print("[fetch_squad] no fixtures returned — this provider has no WC2026 data on your plan yet, "
              "or league/season id differs. (Lineups stay hidden until data exists.)")

    added = 0
    for fxi in fx:
        status = fxi.get("fixture", {}).get("status", {}).get("short", "")
        if status in ("NS", "TBD", "PST", "CANC"):       # not started -> skip
            continue
        fid = fxi["fixture"]["id"]
        hn, an = fxi["teams"]["home"]["name"], fxi["teams"]["away"]["name"]
        ch, ca = canon(hn, fixture_names), canon(an, fixture_names)
        if not ch or not ca:
            continue
        if (ch, ca) in pair_set:
            key, swap = f"{ch}|{ca}", False
        elif (ca, ch) in pair_set:
            key, swap = f"{ca}|{ch}", True
        else:
            continue
        # cache: skip finished matches already stored
        if key in existing and existing[key].get("status") == "FT" and status == "FT":
            continue
        try:
            lu = api_get("/fixtures/lineups", {"fixture": fid}).get("response", [])
            ev = api_get("/fixtures/events", {"fixture": fid}).get("response", [])
        except Exception as e:
            print(f"[fetch_squad] {key}: detail fetch failed: {e}")
            continue
        rec = {"status": status, "events": parse_events(ev, hn, an)}
        for blk in lu:
            side = "home" if blk.get("team", {}).get("name") == hn else "away"
            rec[side] = parse_lineup(blk)
        if swap:                                          # our key has teams in opposite order
            rec["home"], rec["away"] = rec.get("away"), rec.get("home")
            for it in rec["events"]:
                it["team"] = "home" if it["team"] == "away" else "away"
        existing[key] = rec
        added += 1
        time.sleep(1)                                     # be gentle on the free tier

    json.dump(existing, open(path, "w"), indent=1)
    print(f"[fetch_squad] updated {added} match(es); {len(existing)} total in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
