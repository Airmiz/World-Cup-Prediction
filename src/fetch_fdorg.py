"""Fetch formations, lineups, bookings and substitutions for WC2026 matches from
football-data.org, whose FREE tier includes the FIFA World Cup (competition code
WC). Writes data/lineups.json in the shape the Match Centre already renders.

No-ops cleanly when FOOTBALL_DATA_KEY is absent. Free tier = 10 calls/min, so we
cache finished matches and space requests out. Standard library only.

Set the key as a GitHub Actions secret named FOOTBALL_DATA_KEY (free token from
football-data.org/client/register).
"""
import csv
import json
import os
import sys
import time
import unicodedata
import urllib.request

BASE = "https://api.football-data.org/v4"
KEY = os.environ.get("FOOTBALL_DATA_KEY", "").strip()

ALIASES = {
    "usa": "United States", "south korea": "South Korea", "korea republic": "South Korea",
    "ir iran": "Iran", "iran": "Iran", "turkiye": "Turkey", "turkey": "Turkey",
    "czechia": "Czech Republic", "czech republic": "Czech Republic",
    "bosnia and herzegovina": "Bosnia and Herzegovina", "bosnia herzegovina": "Bosnia and Herzegovina",
    "ivory coast": "Ivory Coast", "cote divoire": "Ivory Coast",
    "cape verde": "Cape Verde", "dr congo": "DR Congo", "congo dr": "DR Congo",
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
    # loose contains match (e.g. "Korea Republic" vs "South Korea" already aliased)
    for fn in fixture_names:
        if n and (norm(fn) in n or n in norm(fn)):
            return fn
    return None


def pos_bucket(p):
    p = (p or "").lower()
    if "keeper" in p:
        return "G"
    if "back" in p or "defence" in p or "defender" in p:
        return "D"
    if "midfield" in p:
        return "M"
    if "wing" in p or "forward" in p or "striker" in p or "offence" in p or "attack" in p:
        return "F"
    return "M"


def api_get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"X-Auth-Token": KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def parse_team(block):
    xi = [{"name": p.get("name"), "num": p.get("shirtNumber"), "pos": pos_bucket(p.get("position"))}
          for p in (block.get("lineup") or [])]
    subs = [{"name": p.get("name"), "num": p.get("shirtNumber"), "pos": pos_bucket(p.get("position"))}
            for p in (block.get("bench") or [])]
    return {"formation": block.get("formation") or "", "xi": xi, "subs": subs}


def parse_events(match, home_id):
    out = []
    for g in match.get("goals") or []:
        side = "home" if g.get("team", {}).get("id") == home_id else "away"
        gt = (g.get("type") or "").lower()           # REGULAR / OWN / PENALTY
        detail = "Own Goal" if "own" in gt else ("Penalty" if "pen" in gt else "Normal Goal")
        item = {"min": (g.get("minute") or 0), "team": side, "type": "goal",
                "detail": detail, "player": (g.get("scorer") or {}).get("name")}
        if (g.get("assist") or {}).get("name"):
            item["assist"] = g["assist"]["name"]
        out.append(item)
    for b in match.get("bookings") or []:
        side = "home" if b.get("team", {}).get("id") == home_id else "away"
        card = "red" if "red" in (b.get("card") or "").lower() else "yellow"
        out.append({"min": (b.get("minute") or 0), "team": side, "type": "card",
                    "card": card, "player": (b.get("player") or {}).get("name")})
    for s in match.get("substitutions") or []:
        side = "home" if s.get("team", {}).get("id") == home_id else "away"
        out.append({"min": (s.get("minute") or 0), "team": side, "type": "subst",
                    "player": (s.get("playerOut") or {}).get("name"),
                    "assist": (s.get("playerIn") or {}).get("name")})
    out.sort(key=lambda e: e["min"])
    return out


def main():
    if not KEY:
        print("[fetch_fdorg] FOOTBALL_DATA_KEY not set — skipping.")
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
        ms = api_get("/competitions/WC/matches?season=2026").get("matches", [])
    except Exception as e:
        print(f"[fetch_fdorg] competition fetch failed: {e}")
        return 0
    print(f"[fetch_fdorg] WC matches returned: {len(ms)}")

    updated = 0
    for m in ms:
        status = m.get("status", "")
        if status in ("SCHEDULED", "TIMED", "POSTPONED", "CANCELLED"):
            continue
        hn = (m.get("homeTeam") or {}).get("name")
        an = (m.get("awayTeam") or {}).get("name")
        ch, ca = canon(hn, fixture_names), canon(an, fixture_names)
        if not ch or not ca:
            continue
        if (ch, ca) in pair_set:
            key, swap = f"{ch}|{ca}", False
        elif (ca, ch) in pair_set:
            key, swap = f"{ca}|{ch}", True
        else:
            continue
        if existing.get(key, {}).get("status") == "FINISHED" and status == "FINISHED":
            continue                                   # cached
        try:
            full = api_get(f"/matches/{m['id']}")
            match = full.get("match") or full          # v4 wraps in {match:...} on some plans
        except Exception as e:
            print(f"[fetch_fdorg] {key}: detail failed: {e}")
            continue
        home_id = (match.get("homeTeam") or {}).get("id")
        rec = {"status": status,
               "home": parse_team(match.get("homeTeam") or {}),
               "away": parse_team(match.get("awayTeam") or {}),
               "events": parse_events(match, home_id)}
        if swap:
            rec["home"], rec["away"] = rec["away"], rec["home"]
            for e in rec["events"]:
                e["team"] = "home" if e["team"] == "away" else "away"
        # only store if we actually got useful detail (lineup or events)
        has_xi = rec["home"]["xi"] or rec["away"]["xi"]
        if has_xi or rec["events"]:
            existing[key] = rec
            updated += 1
        time.sleep(7)                                  # stay under 10 calls/min

    json.dump(existing, open(path, "w"), indent=1)
    note = "" if updated else " (no lineup/event detail available on this tier yet)"
    print(f"[fetch_fdorg] updated {updated} match(es){note}; {len(existing)} total in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
