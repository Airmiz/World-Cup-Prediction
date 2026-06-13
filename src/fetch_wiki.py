"""Best-effort lineup/cards/subs fetcher from Wikipedia (free + legitimate).

Wikipedia content is CC BY-SA and its API is built for reuse. World Cup match
articles embed {{Football box collapsible}} templates whose lineup fields contain
the starting XI, substitutes, bookings and substitutions. This parses them into
data/lineups.json (same shape the Match Centre renders), with attribution.

Caveats (be honest): Wikipedia is editor-populated, so it lags live by hours; and
lineup markup varies by match, so extraction is best-effort — when a match can't
be parsed cleanly it's simply skipped (never guessed, never breaks the pipeline).
Richer/cleaner sources (the paid API path) still take priority if present.

Standard library only.  Usage: python3 src/fetch_wiki.py [--selftest]
"""
import csv
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request

UA = "WC2026-tracker/1.0 (open-source fan project; contact via GitHub)"
API = "https://en.wikipedia.org/w/api.php"

POS_RE = re.compile(r"\b(GK|RWB|LWB|RB|LB|CB|RCB|LCB|SW|DF|DM|CDM|CM|RM|LM|AM|CAM|MF|RW|LW|CF|SS|ST|FW)\b")
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
YEL_RE = re.compile(r"\{\{\s*(?:yel|yellow card|yellow)\s*\|?\s*(\d+)?", re.I)
RED_RE = re.compile(r"\{\{\s*(?:sent off|red card|red|dismissed|sent-off)\s*\|?\s*(\d+)?", re.I)
SUBON_RE = re.compile(r"\{\{\s*(?:subon|sub on|substitute on|in)\s*\|?\s*(\d+)?", re.I)
SUBOFF_RE = re.compile(r"\{\{\s*(?:suboff|sub off|substitute off|out)\s*\|?\s*(\d+)?", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    for ch in ".-&/'":
        s = s.replace(ch, " ")
    return " ".join(s.split())


def pos_bucket(tok):
    t = (tok or "").upper()
    if t == "GK":
        return "G"
    if t in ("RB", "LB", "CB", "RCB", "LCB", "RWB", "LWB", "SW", "DF"):
        return "D"
    if t in ("DM", "CDM", "CM", "RM", "LM", "AM", "CAM", "MF"):
        return "M"
    return "F"


def api_wikitext(title, retries=2):
    q = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "wikitext",
                                "format": "json", "formatversion": "2"})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode()).get("parse", {}).get("wikitext", "")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                time.sleep(6 * (attempt + 1)); continue
            raise


def find_boxes(wikitext):
    """Yield the inner text of each {{Football box collapsible ...}} template."""
    out, i, key = [], 0, "{{football box collapsible"
    low = wikitext.lower()
    while True:
        s = low.find(key, i)
        if s < 0:
            break
        depth, j = 0, s
        while j < len(wikitext):
            if wikitext[j:j + 2] == "{{":
                depth += 1; j += 2; continue
            if wikitext[j:j + 2] == "}}":
                depth -= 1; j += 2
                if depth == 0:
                    break
                continue
            j += 1
        out.append(wikitext[s:j]); i = j
    return out


def split_params(block):
    """Top-level |key=value split, respecting nested {{}} and [[]]."""
    params, depth, buf = {}, 0, ""
    body = block[2:-2] if block.startswith("{{") else block
    parts, cur = [], ""
    k = 0
    while k < len(body):
        two = body[k:k + 2]
        if two in ("{{", "[["):
            depth += 1; cur += two; k += 2; continue
        if two in ("}}", "]]"):
            depth -= 1; cur += two; k += 2; continue
        if body[k] == "|" and depth == 0:
            parts.append(cur); cur = ""; k += 1; continue
        cur += body[k]; k += 1
    parts.append(cur)
    for p in parts:
        if "=" in p:
            key, _, val = p.partition("=")
            params[key.strip().lower()] = val.strip()
    return params


def parse_lineup(text):
    """Parse one team's lineup field -> (xi, subs, events_fragments)."""
    if not text:
        return [], [], []
    # split starters vs substitutes
    m = re.split(r"'''?\s*Substitutions?\s*:?\s*'''?|Substitutes?:", text, 1, re.I)
    starters_txt, subs_txt = m[0], (m[1] if len(m) > 1 else "")
    subs_txt = re.split(r"'''?\s*(?:Manager|Head coach)\s*:?", subs_txt, 1, re.I)[0]

    def players(seg, started):
        rows, ev = [], []
        # walk line by line so position tokens & cards attach to the right player
        for line in re.split(r"<br\s*/?>|\n", seg):
            link = LINK_RE.search(line)
            if not link:
                continue
            name = (link.group(2) or link.group(1)).strip()
            if not name or name.lower().startswith(("file:", "image:")):
                continue
            posm = POS_RE.search(line)
            pos = pos_bucket(posm.group(1)) if posm else ("G" if not rows and started else "M")
            rows.append({"name": name, "pos": pos})
            for rx, kind in ((YEL_RE, "yellow"), (RED_RE, "red")):
                mm = rx.search(line)
                if mm:
                    ev.append({"type": "card", "card": kind, "player": name,
                               "min": int(mm.group(1)) if mm.group(1) else 0})
            on, off = SUBON_RE.search(line), SUBOFF_RE.search(line)
            if on:
                ev.append({"type": "sub", "dir": "on", "player": name,
                           "min": int(on.group(1)) if on.group(1) else 0})
            if off:
                ev.append({"type": "sub", "dir": "off", "player": name,
                           "min": int(off.group(1)) if off.group(1) else 0})
        return rows, ev

    xi, ev1 = players(starters_txt, True)
    subs, ev2 = players(subs_txt, False)
    return xi[:11], subs, ev1 + ev2


def formation(xi):
    d = sum(1 for p in xi if p["pos"] == "D")
    mi = sum(1 for p in xi if p["pos"] == "M")
    f = sum(1 for p in xi if p["pos"] == "F")
    return f"{d}-{mi}-{f}" if (d or mi or f) else ""


def pair_events(frag, team):
    """Turn per-player fragments into Match-Centre events for one side."""
    out = []
    for e in frag:
        if e["type"] == "card":
            out.append({"min": e["min"], "team": team, "type": "card",
                        "card": e["card"], "player": e["player"]})
    offs = [e for e in frag if e.get("dir") == "off"]
    ons = [e for e in frag if e.get("dir") == "on"]
    for i, on in enumerate(ons):
        off = offs[i] if i < len(offs) else {}
        out.append({"min": on["min"] or off.get("min", 0), "team": team, "type": "subst",
                    "player": off.get("player"), "assist": on["player"]})
    return out


def build_record(box_params):
    home = parse_lineup(box_params.get("lineup1", ""))
    away = parse_lineup(box_params.get("lineup2", ""))
    xi_h, subs_h, frag_h = home
    xi_a, subs_a, frag_a = away
    if not xi_h and not xi_a:
        return None
    rec = {"status": "FINISHED", "source": "wikipedia",
           "home": {"formation": formation(xi_h), "xi": xi_h, "subs": subs_h},
           "away": {"formation": formation(xi_a), "xi": xi_a, "subs": subs_a},
           "events": pair_events(frag_h, "home") + pair_events(frag_a, "away")}
    return rec


# ---------------------------------------------------------------- selftest
SAMPLE = """{{Football box collapsible
|team1=Qatar |score=0–2 |team2=Ecuador
|lineup1=
'''GK''' [[Saad Al-Sheeb]]<br/>
'''RB''' [[Pedro Miguel]]<br/>
'''CB''' [[Boualem Khoukhi]] {{yel|45}}<br/>
'''CM''' [[Karim Boudiaf]] {{suboff|60}}<br/>
'''CF''' [[Almoez Ali]]<br/>
'''Substitutions:'''
[[Mohammed Muntari]] {{subon|60}}<br/>
'''Manager:''' [[Félix Sánchez Bas]]
|lineup2=
'''GK''' [[Hernán Galíndez]]<br/>
'''CB''' [[Félix Torres]]<br/>
'''CF''' [[Enner Valencia]] {{yel|70}}<br/>
'''Substitutions:'''
[[Kevin Rodríguez]] {{subon|80}}
}}"""


def selftest():
    boxes = find_boxes(SAMPLE)
    assert len(boxes) == 1, boxes
    p = split_params(boxes[0])
    assert p["team1"] == "Qatar" and p["team2"] == "Ecuador", p.get("team1")
    rec = build_record(p)
    assert [x["name"] for x in rec["home"]["xi"]] == \
        ["Saad Al-Sheeb", "Pedro Miguel", "Boualem Khoukhi", "Karim Boudiaf", "Almoez Ali"]
    assert rec["home"]["xi"][0]["pos"] == "G" and rec["home"]["xi"][2]["pos"] == "D"
    cards = [e for e in rec["events"] if e["type"] == "card"]
    subs = [e for e in rec["events"] if e["type"] == "subst"]
    assert any(c["player"] == "Boualem Khoukhi" and c["card"] == "yellow" for c in cards), cards
    assert any(s["assist"] == "Mohammed Muntari" and s["player"] == "Karim Boudiaf" for s in subs), subs
    assert rec["home"]["formation"] == "2-1-1", rec["home"]["formation"]
    print("[fetch_wiki] selftest PASSED — parsed XI, cards, subs, formation correctly")


# ---------------------------------------------------------------- main
def article_for(group):
    return f"2026 FIFA World Cup Group {group}"


def main():
    if "--selftest" in sys.argv:
        selftest(); return 0

    fixtures, played = [], []
    with open("data/results.csv") as f:
        for row in csv.DictReader(f):
            if row["tournament"] == "FIFA World Cup" and row["date"] >= "2026-06-01":
                fixtures.append((row["home_team"], row["away_team"]))
                if row.get("home_score") not in ("", None) and row["home_score"] != "NA":
                    played.append((row["home_team"], row["away_team"]))
    groups = json.load(open("data/tournament.json"))["groups"]
    group_of = {t: g for g, ts in groups.items() for t in ts}
    pair_set = {(h, a) for h, a in fixtures}
    names = sorted({t for p in fixtures for t in p})

    def canon(n):
        nn = norm(n)
        for fn in names:
            if norm(fn) == nn or norm(fn) in nn or nn in norm(fn):
                return fn
        return None

    path = "data/lineups.json"
    existing = json.load(open(path)) if os.path.exists(path) else {}
    # only fetch group articles for played matches we don't already have lineups for
    needed_groups = sorted({group_of[h] for h, a in played if f"{h}|{a}" not in existing})
    if not needed_groups:
        print("[fetch_wiki] nothing to fetch — all played matches already have lineups")
        return 0
    updated = 0
    for g in needed_groups:
        try:
            wt = api_wikitext(article_for(g))
        except Exception as e:
            print(f"[fetch_wiki] group {g} fetch failed: {e}")
            continue
        for box in find_boxes(wt):
            p = split_params(box)
            ch, ca = canon(p.get("team1", "")), canon(p.get("team2", ""))
            if not ch or not ca:
                continue
            if (ch, ca) in pair_set:
                key, swap = f"{ch}|{ca}", False
            elif (ca, ch) in pair_set:
                key, swap = f"{ca}|{ch}", True
            else:
                continue
            # don't overwrite richer data from a paid provider
            if existing.get(key, {}).get("source") in ("espn", "api-football", "football-data"):
                continue
            rec = build_record(p)
            if not rec:
                continue
            if swap:
                rec["home"], rec["away"] = rec["away"], rec["home"]
                for e in rec["events"]:
                    e["team"] = "home" if e["team"] == "away" else "away"
            existing[key] = rec
            updated += 1
        time.sleep(3)

    json.dump(existing, open(path, "w"), indent=1)
    note = "" if updated else " (no parseable lineups yet — Wikipedia fills in after matches)"
    print(f"[fetch_wiki] updated {updated} match(es) from Wikipedia{note}; {len(existing)} total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
