"""Automatically fetch real goal minutes for played WC2026 matches and merge
them into data/goal_events.json (used by the win-probability charts).

Source: the open openfootball dataset (free, no API key, GitHub-hosted JSON):
  https://github.com/openfootball/worldcup.json  ->  2026/worldcup.json
Each match exposes goals1 (home) / goals2 (away) with a `minute` (+`offset` for
stoppage). We normalise team names to our fixture names, convert to the
{"min","team"} format, and add any match not already recorded. Existing
(hand-curated) entries are preserved.

Runs with only the Python standard library so it works in any CI environment.
Usage: python3 src/fetch_goals.py [--source URL] [--print-only]
"""
import json
import os
import sys
import unicodedata
import urllib.request

SOURCES = [
    "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json",
    "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026--north-america/worldcup.json",
]

# openfootball name -> our fixture name (extend as needed)
ALIASES = {
    "usa": "United States", "united states of america": "United States",
    "korea republic": "South Korea", "south korea": "South Korea",
    "ir iran": "Iran", "iran": "Iran",
    "bosnia": "Bosnia and Herzegovina", "bosnia and herzegovina": "Bosnia and Herzegovina",
    "bosnia herzegovina": "Bosnia and Herzegovina",
    "dr congo": "DR Congo", "congo dr": "DR Congo",
    "cape verde": "Cape Verde", "cabo verde": "Cape Verde",
    "ivory coast": "Ivory Coast", "cote d'ivoire": "Ivory Coast",
    "turkiye": "Turkey", "turkey": "Turkey",
    "czechia": "Czech Republic", "czech republic": "Czech Republic",
}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()
    for ch in ".-&/":
        s = s.replace(ch, " ")
    return " ".join(s.split())


def canon(name, fixture_names):
    """Map an openfootball team name to one of our fixture team names."""
    n = norm(name)
    if n in ALIASES:
        return ALIASES[n]
    for fn in fixture_names:
        if norm(fn) == n:
            return fn
    return None


def fetch_source():
    for url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "wc2026-bot"})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    return json.loads(r.read().decode()), url
        except Exception as e:
            print(f"[fetch_goals] {url} -> {e}", file=sys.stderr)
    return None, None


def events_from_match(m):
    """Return [{'min','team'}...] from an openfootball match, or None if not played."""
    sc = m.get("score", {})
    if "ft" not in sc:
        return None
    ev = []
    for arr, team in (("goals1", "home"), ("goals2", "away")):
        for g in m.get(arr, []) or []:
            mn = parse_minute(g.get("minute"))
            if mn is None:
                continue
            e = {"min": mn, "team": team}
            if g.get("name"):
                e["name"] = g["name"]
            if g.get("owngoal"):
                e["og"] = True
            if g.get("penalty"):
                e["pen"] = True
            ev.append(e)
    ev.sort(key=lambda e: e["min"])
    return ev


def parse_minute(mn):
    """Handle ints, '45+5' stoppage strings, etc. -> minute capped at 90."""
    if mn is None:
        return None
    try:
        if isinstance(mn, str):
            mn = mn.split("+")[0].strip()
        return min(int(mn), 90)
    except (ValueError, TypeError):
        return None


def main():
    src_override = None
    print_only = "--print-only" in sys.argv
    if "--source" in sys.argv:
        src_override = sys.argv[sys.argv.index("--source") + 1]

    # our fixtures (exact home/away names)
    fixtures = []
    try:
        import csv
        with open("data/results.csv") as f:
            for row in csv.DictReader(f):
                if row["tournament"] == "FIFA World Cup" and row["date"] >= "2026-06-01":
                    fixtures.append((row["home_team"], row["away_team"]))
    except FileNotFoundError:
        pass
    fixture_names = sorted({t for pair in fixtures for t in pair})
    pair_set = {(h, a) for h, a in fixtures}

    if src_override:
        with open(src_override) as f:
            data = json.load(f)
        src = src_override
    else:
        data, src = fetch_source()
    if not data:
        print("[fetch_goals] no source reachable; leaving goal_events.json unchanged")
        return 0
    print(f"[fetch_goals] source: {src}")

    parsed = {}
    for m in data.get("matches", []):
        t1, t2 = m.get("team1"), m.get("team2")
        ev = events_from_match(m)
        if not t1 or not t2 or ev is None:
            continue
        c1, c2 = canon(t1, fixture_names), canon(t2, fixture_names)
        if not c1 or not c2:
            continue
        if (c1, c2) in pair_set:
            parsed[f"{c1}|{c2}"] = ev
        elif (c2, c1) in pair_set:                      # listed reversed -> swap sides
            parsed[f"{c2}|{c1}"] = [{"min": e["min"], "team": "home" if e["team"] == "away" else "away"} for e in ev]

    path = "data/goal_events.json"
    existing = json.load(open(path)) if os.path.exists(path) else {}
    changed = []
    for k, ev in parsed.items():                         # source (with scorer names) wins
        if existing.get(k) != ev:
            existing[k] = ev
            changed.append(k)

    if print_only:
        print(json.dumps(parsed, indent=1))
        return 0
    if changed:
        json.dump(existing, open(path, "w"), indent=2)
    print(f"[fetch_goals] matched {len(parsed)} matches; updated {len(changed)}: {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
