"""Fetch lineups, formations, cards and substitutions from ESPN's soccer JSON API.

ESPN exposes a structured (undocumented) JSON API at site.api.espn.com that returns,
once a match is live/finished: each team's formation + full roster (with starter flag,
jersey, position) and a keyEvents list (goals/cards/subs). This maps it into
data/lineups.json (the shape the Match Centre renders).

NOTE: this is ESPN's *undocumented* endpoint; their Terms restrict automated use, so it's
used here at the project owner's discretion for a non-commercial fan project, with an
on-page "data via ESPN" credit. It's best-effort and may change; it never overwrites a
paid-provider entry, and skips anything it can't parse.

Standard library only.  Usage: python3 src/fetch_espn.py [--selftest]
"""
import csv
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request

UA = "WC2026-tracker/1.0 (non-commercial fan project)"
LEAGUE = "fifa.world"
SB = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{LEAGUE}/scoreboard"
SUM = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{LEAGUE}/summary"

ALIASES = {
    "usa": "United States", "united states": "United States",
    "korea republic": "South Korea", "south korea": "South Korea",
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
    for fn in fixture_names:
        if n and (norm(fn) in n or n in norm(fn)):
            return fn
    return None


# per-player match stats we surface (ESPN name -> short column label)
PLAYER_STATS = [
    ("totalGoals", "G"), ("goalAssists", "A"), ("totalShots", "SH"),
    ("shotsOnTarget", "SOT"), ("foulsCommitted", "FC"), ("foulsSuffered", "FS"),
    ("offsides", "OFF"), ("yellowCards", "YC"), ("redCards", "RC"),
    ("saves", "SV"), ("goalsConceded", "GC"),
]

# team match stats we surface, in display order (ESPN name -> nice label, is-percentage)
TEAM_STATS = [
    ("possessionPct", "Possession", True), ("totalShots", "Shots", False),
    ("shotsOnTarget", "Shots on Target", False), ("wonCorners", "Corners", False),
    ("totalPasses", "Passes", False), ("foulsCommitted", "Fouls", False),
    ("offsides", "Offsides", False), ("yellowCards", "Yellow Cards", False),
    ("redCards", "Red Cards", False), ("totalTackles", "Tackles", False),
    ("interceptions", "Interceptions", False), ("saves", "Saves", False),
]


def player_stats(p):
    """Curated per-player match stats dict (only if ESPN provided any)."""
    raw = {s.get("name"): s.get("displayValue") for s in (p.get("stats") or [])}
    if not raw:
        return None
    out = {}
    for name, col in PLAYER_STATS:
        v = raw.get(name)
        if v in (None, ""):
            continue
        try:
            out[col] = int(float(v))
        except (TypeError, ValueError):
            out[col] = v
    return out or None


def pos_bucket(name):
    n = (name or "").lower()
    if "keeper" in n or "goal" in n:
        return "G"
    if "defend" in n or "back" in n or "sweeper" in n:
        return "D"
    if "midfield" in n:
        return "M"
    if any(w in n for w in ("forward", "striker", "wing", "attack")):
        return "F"
    return "M"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def minute(ev):
    c = (ev.get("clock") or {}).get("displayValue") or ev.get("time") or ""
    m = re.search(r"(\d+)", str(c))
    return int(m.group(1)) if m else 0


def parse_summary(summ, our_home, our_away):
    """Map an ESPN summary payload to our lineups.json record (or None)."""
    rosters = summ.get("rosters") or []
    if not rosters:
        return None
    side_team = {}     # ESPN team displayName -> 'home'/'away' (ESPN's own)
    blocks = {}
    for r in rosters:
        ha = r.get("homeAway")
        tname = (r.get("team") or {}).get("displayName", "")
        side_team[tname] = ha
        xi, subs = [], []
        for p in r.get("roster") or []:
            ath = (p.get("athlete") or {}).get("displayName")
            if not ath:
                continue
            posn = (p.get("position") or {})
            entry = {"name": ath, "num": p.get("jersey"),
                     "pos": pos_bucket(posn.get("displayName") or posn.get("name") or posn.get("abbreviation"))}
            ps = player_stats(p)
            if ps:
                entry["st"] = ps
            (xi if p.get("starter") else subs).append(entry)
        blocks[ha] = {"formation": r.get("formation") or "", "xi": xi[:11], "subs": subs}
    if "home" not in blocks and "away" not in blocks:
        return None

    events = []
    for ev in (summ.get("keyEvents") or summ.get("commentary") or []):
        t = ev.get("type") or {}
        ttype = (t.get("type") or t.get("text") or "").lower()   # e.g. yellow-card, substitution, penalty-goal, own-goal
        tname = (ev.get("team") or {}).get("displayName", "")
        side = side_team.get(tname)
        if side is None:
            continue
        who = [(p.get("athlete") or {}).get("displayName") for p in (ev.get("participants") or [])
               if (p.get("athlete") or {}).get("displayName")]
        mn = minute(ev)
        is_goal = ev.get("scoringPlay") is True or ("goal" in ttype and "no goal" not in ttype)
        if "own goal" in ttype:
            events.append({"min": mn, "team": side, "type": "goal", "detail": "Own Goal",
                           "player": who[0] if who else None})
        elif is_goal:  # "penalty---scored" has no "goal" in its type string, so trust ESPN's scoringPlay flag
            events.append({"min": mn, "team": side, "type": "goal",
                           "detail": "Penalty" if "penalt" in ttype else "Normal Goal",
                           "player": who[0] if who else None,
                           **({"assist": who[1]} if len(who) > 1 else {})})
        elif "yellow" in ttype:
            events.append({"min": mn, "team": side, "type": "card", "card": "yellow",
                           "player": who[0] if who else None})
        elif "red" in ttype:
            events.append({"min": mn, "team": side, "type": "card", "card": "red",
                           "player": who[0] if who else None})
        elif "substitut" in ttype:
            # ESPN lists [in, out] for subs
            events.append({"min": mn, "team": side, "type": "subst",
                           "assist": who[0] if who else None,
                           "player": who[1] if len(who) > 1 else None})

    # Reconcile card events against the authoritative per-player boxscore counts.
    # ESPN's keyEvents include VAR reviews (e.g. "VAR - (Red) Card Upgrade") that may be
    # overturned; the player's own yellowCards/redCards tally is the source of truth, so a
    # card event for a player whose tally doesn't back it up is dropped (never invented).
    cardtally = {}
    for r in rosters:
        for p in r.get("roster") or []:
            nm = (p.get("athlete") or {}).get("displayName")
            if not nm:
                continue
            raw = {s.get("name"): s.get("displayValue") for s in (p.get("stats") or [])}
            if raw:
                def _i(k):
                    try:
                        return int(float(raw.get(k)))
                    except (TypeError, ValueError):
                        return 0
                cardtally[norm(nm)] = {"yellow": _i("yellowCards"), "red": _i("redCards")}

    def _card_confirmed(e):
        if e.get("type") != "card":
            return True
        tally = cardtally.get(norm(e.get("player") or ""))
        if not tally:                       # no per-player stats → keep (can't verify)
            return True
        return tally.get(e.get("card"), 0) > 0
    events = [e for e in events if _card_confirmed(e)]

    # team match stats from the boxscore (possession, shots, passes, …)
    teamstats = {"home": {}, "away": {}, "labels": {}, "pct": {}}
    for t in ((summ.get("boxscore") or {}).get("teams") or []):
        side = side_team.get((t.get("team") or {}).get("displayName", ""))
        if side is None:
            continue
        have = {s.get("name"): s for s in (t.get("statistics") or []) if s.get("name")}
        for name, label, is_pct in TEAM_STATS:
            s = have.get(name)
            if not s or s.get("displayValue") in (None, ""):
                continue
            teamstats[side][name] = s.get("displayValue")
            teamstats["labels"][name] = label
            teamstats["pct"][name] = is_pct
    has_team_stats = bool(teamstats["home"] or teamstats["away"])

    rec = {"status": "FINISHED", "source": "espn",
           "home": blocks.get("home", {"formation": "", "xi": [], "subs": []}),
           "away": blocks.get("away", {"formation": "", "xi": [], "subs": []}),
           "events": events}
    if has_team_stats:
        rec["teamstats"] = teamstats
    return rec


PROVIDERS = ("espn", "api-football", "football-data")
SCHEDULE = "output/match_predictions.csv"


def load_schedule():
    """Full WC2026 fixture list with our canonical home/away orientation + match date.

    Prefers output/match_predictions.csv (all 72 group fixtures, scheduled or not) so live
    and just-finished matches can be mapped even before they appear in results.csv. Falls
    back to results.csv (played matches only) if the schedule file is missing.
    """
    fixtures = []  # (home, away, "YYYYMMDD")
    if os.path.exists(SCHEDULE):
        with open(SCHEDULE) as f:
            for row in csv.DictReader(f):
                h, a = row.get("home_team"), row.get("away_team")
                d = (row.get("date") or row.get("utc_kickoff") or "")[:10].replace("-", "")
                if h and a and len(d) == 8:
                    fixtures.append((h, a, d))
    if not fixtures and os.path.exists("data/results.csv"):
        with open("data/results.csv") as f:
            for row in csv.DictReader(f):
                if row["tournament"] == "FIFA World Cup" and row["date"] >= "2026-06-01":
                    fixtures.append((row["home_team"], row["away_team"], row["date"].replace("-", "")))
    return fixtures


def main():
    if "--selftest" in sys.argv:
        selftest(); return 0

    fixtures = load_schedule()
    if not fixtures:
        print("[fetch_espn] no schedule found"); return 0
    names = sorted({t for h, a, _ in fixtures for t in (h, a)})
    pair_set = {(h, a) for h, a, _ in fixtures}

    path = "data/lineups.json"
    existing = json.load(open(path)) if os.path.exists(path) else {}

    def is_final(key):
        e = existing.get(key) or {}
        return bool(e.get("final")) and e.get("source") in PROVIDERS

    # Only scan dates that could have new data: a fixture's date that has arrived (UTC) and
    # whose match isn't already stored as final. Past finals drop out → fewer calls over time.
    today = time.strftime("%Y%m%d", time.gmtime())
    scan_dates = sorted({d for h, a, d in fixtures if d <= today and not is_final(f"{h}|{a}")})
    if not scan_dates:
        print(f"[fetch_espn] nothing to scan — all {len(fixtures)} fixtures up to today are final")
        return 0

    # Map fixtures -> (ESPN gameId, swap, state) via the scoreboard for each scan date.
    # state: "pre" (not started), "in" (live), "post" (finished).
    gameids = {}
    for d in scan_dates:
        try:
            sb = get(f"{SB}?dates={d}")
        except Exception as e:
            print(f"[fetch_espn] scoreboard {d} failed: {e}"); continue
        for ev in sb.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            cs = comp.get("competitors", [])
            state = (((ev.get("status") or {}).get("type") or {}).get("state") or "").lower()
            h = next((c["team"]["displayName"] for c in cs if c.get("homeAway") == "home"), None)
            a = next((c["team"]["displayName"] for c in cs if c.get("homeAway") == "away"), None)
            ch, ca = canon(h, names), canon(a, names)
            if ch and ca:
                if (ch, ca) in pair_set:
                    gameids[f"{ch}|{ca}"] = (ev.get("id"), False, state)
                elif (ca, ch) in pair_set:
                    gameids[f"{ca}|{ch}"] = (ev.get("id"), True, state)
        time.sleep(1)

    # Fetch every live/finished match that isn't already stored as final.
    need = [(k, v) for k, v in gameids.items()
            if v[2] in ("in", "post") and not is_final(k)]
    if not need:
        print(f"[fetch_espn] nothing to update — {sum(is_final(k) for k in gameids)} mapped match(es) already final")
        return 0

    updated = 0
    for key, (gid, swap, state) in need:
        h, a = key.split("|", 1)
        try:
            rec = parse_summary(get(f"{SUM}?event={gid}"), h, a)
        except Exception as e:
            print(f"[fetch_espn] {key} summary failed: {e}"); continue
        if not rec or (not rec["home"]["xi"] and not rec["away"]["xi"] and not rec["events"]):
            continue
        if swap:
            rec["home"], rec["away"] = rec["away"], rec["home"]
            if rec.get("teamstats"):
                ts = rec["teamstats"]
                ts["home"], ts["away"] = ts["away"], ts["home"]
            for e in rec["events"]:
                e["team"] = "home" if e["team"] == "away" else "away"
        rec["final"] = (state == "post")
        rec["status"] = "FINISHED" if state == "post" else "LIVE"
        existing[key] = rec
        updated += 1
        time.sleep(1)

    json.dump(existing, open(path, "w"), indent=1)
    finals = sum(1 for k in gameids if is_final(k) or (gameids[k][2] == "post"))
    print(f"[fetch_espn] updated {updated} match(es); {len(existing)} stored, {finals} final")
    return 0


# ---------------------------------------------------------------- selftest
SAMPLE = {
 "rosters": [
   {"homeAway": "home", "team": {"displayName": "United States"}, "formation": "4-3-3",
    "roster": [
      {"starter": True, "jersey": "1", "athlete": {"displayName": "Matt Turner"}, "position": {"displayName": "Goalkeeper"}},
      {"starter": True, "jersey": "9", "athlete": {"displayName": "Folarin Balogun"}, "position": {"displayName": "Center Forward"},
       "stats": [{"name": "totalGoals", "displayValue": "2"}, {"name": "totalShots", "displayValue": "5"},
                 {"name": "shotsOnTarget", "displayValue": "3"}, {"name": "goalAssists", "displayValue": "0"}]},
      {"starter": True, "jersey": "3", "athlete": {"displayName": "Chris Richards"}, "position": {"displayName": "Center Left Defender"},
       "stats": [{"name": "redCards", "displayValue": "0"}, {"name": "yellowCards", "displayValue": "0"}]},
      {"starter": False, "jersey": "19", "athlete": {"displayName": "Haji Wright"}, "position": {"displayName": "Forward"}}]},
   {"homeAway": "away", "team": {"displayName": "Paraguay"}, "formation": "4-4-2",
    "roster": [{"starter": True, "jersey": "1", "athlete": {"displayName": "Roberto Fernandez"}, "position": {"displayName": "Goalkeeper"}}]}],
 "boxscore": {"teams": [
   {"team": {"displayName": "United States"}, "statistics": [
     {"name": "possessionPct", "label": "Possession", "displayValue": "65.3"},
     {"name": "totalShots", "label": "SHOTS", "displayValue": "16"},
     {"name": "wonCorners", "label": "Corner Kicks", "displayValue": "3"}]},
   {"team": {"displayName": "Paraguay"}, "statistics": [
     {"name": "possessionPct", "label": "Possession", "displayValue": "34.7"},
     {"name": "totalShots", "label": "SHOTS", "displayValue": "8"},
     {"name": "wonCorners", "label": "Corner Kicks", "displayValue": "5"}]}]},
 "keyEvents": [
   {"clock": {"displayValue": "31'"}, "type": {"type": "goal", "text": "Goal"}, "team": {"displayName": "United States"},
    "participants": [{"athlete": {"displayName": "Folarin Balogun"}}, {"athlete": {"displayName": "Christian Pulisic"}}]},
   {"clock": {"displayValue": "52'"}, "type": {"type": "yellow-card", "text": "Yellow Card"}, "team": {"displayName": "Paraguay"},
    "participants": [{"athlete": {"displayName": "Andres Cubas"}}]},
   {"clock": {"displayValue": "70'"}, "type": {"type": "substitution", "text": "Substitution"}, "team": {"displayName": "United States"},
    "participants": [{"athlete": {"displayName": "Haji Wright"}}, {"athlete": {"displayName": "Tim Weah"}}]},
   {"clock": {"displayValue": "52'"}, "type": {"type": "var---red-card-upgrade", "text": "VAR - (Red) Card Upgrade"}, "team": {"displayName": "United States"},
    "participants": [{"athlete": {"displayName": "Chris Richards"}}]}]}


def selftest():
    rec = parse_summary(SAMPLE, "United States", "Paraguay")
    assert rec["home"]["formation"] == "4-3-3", rec["home"]["formation"]
    assert [p["name"] for p in rec["home"]["xi"]] == ["Matt Turner", "Folarin Balogun", "Chris Richards"]
    assert rec["home"]["xi"][0]["pos"] == "G" and rec["home"]["xi"][2]["pos"] == "D"
    assert rec["home"]["subs"][0]["name"] == "Haji Wright"
    assert not any(e["type"] == "card" and e.get("player") == "Chris Richards" for e in rec["events"]), \
        "phantom VAR card not reconciled away"
    cards = [e for e in rec["events"] if e["type"] == "card"]
    subs = [e for e in rec["events"] if e["type"] == "subst"]
    goals = [e for e in rec["events"] if e["type"] == "goal"]
    assert goals and goals[0]["player"] == "Folarin Balogun" and goals[0].get("assist") == "Christian Pulisic"
    assert cards and cards[0]["player"] == "Andres Cubas" and cards[0]["card"] == "yellow"
    assert subs and subs[0]["assist"] == "Haji Wright" and subs[0]["player"] == "Tim Weah"
    # player match stats attached to the scorer
    bal = next(p for p in rec["home"]["xi"] if p["name"] == "Folarin Balogun")
    assert bal["st"]["G"] == 2 and bal["st"]["SH"] == 5 and bal["st"]["SOT"] == 3, bal.get("st")
    assert "st" not in rec["home"]["xi"][0], "players without stats must omit st"
    # team match stats comparison
    ts = rec["teamstats"]
    assert ts["home"]["possessionPct"] == "65.3" and ts["away"]["possessionPct"] == "34.7"
    assert ts["home"]["totalShots"] == "16" and ts["labels"]["totalShots"] == "Shots"
    assert ts["pct"]["possessionPct"] is True and ts["pct"]["totalShots"] is False
    print("[fetch_espn] selftest PASSED — formation, XI, subs, cards, goal+assist, team & player stats parsed correctly")


if __name__ == "__main__":
    sys.exit(main())
