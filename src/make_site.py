"""Generate a self-contained single-file website (website/index.html).

Design language: Apple-style — system font stack (SF on Apple devices), light
#f5f5f7 canvas with white cards, frosted-glass sticky nav, large tight-tracked
headlines, soft shadows, pill controls, system-blue accent, automatic dark mode,
gentle scroll-reveal animations.
"""
import base64, json
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# city -> (IANA zone, hours to subtract from ET to get venue-local clock time)
CITY_TZ = {
 "Mexico City":("America/Mexico_City",2),"Zapopan":("America/Mexico_City",2),
 "Guadalajara":("America/Mexico_City",2),"Guadalupe":("America/Monterrey",2),
 "Toronto":("America/Toronto",0),"East Rutherford":("America/New_York",0),
 "Foxborough":("America/New_York",0),"Philadelphia":("America/New_York",0),
 "Atlanta":("America/New_York",0),"Miami Gardens":("America/New_York",0),"Miami":("America/New_York",0),
 "Houston":("America/Chicago",1),"Arlington":("America/Chicago",1),"Kansas City":("America/Chicago",1),
 "Inglewood":("America/Los_Angeles",3),"Los Angeles":("America/Los_Angeles",3),
 "Santa Clara":("America/Los_Angeles",3),"Seattle":("America/Los_Angeles",3),"Vancouver":("America/Vancouver",3),
}

def et_to_utc(date_str, et_hhmm, city):
    """ET clock time on the venue-local date -> UTC ISO string (Z)."""
    zone, shift = CITY_TZ[city]
    eh, em = map(int, et_hhmm.split(":"))
    local_naive = datetime(*map(int, date_str.split("-")), eh, em) - timedelta(hours=shift)
    return local_naive.replace(tzinfo=ZoneInfo(zone)).astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

mp = pd.read_csv("output/match_predictions.csv")
tp = pd.read_csv("output/team_probabilities.csv")
bt = json.load(open("output/backtest.json"))
ss = json.load(open("output/sim_summary.json"))
br = json.load(open("output/bracket.json"))
calib_b64 = base64.b64encode(open("output/fig_calibration.png", "rb").read()).decode()

FLAGS = {
 "Mexico":"🇲🇽","South Africa":"🇿🇦","South Korea":"🇰🇷","Czech Republic":"🇨🇿",
 "Canada":"🇨🇦","Bosnia and Herzegovina":"🇧🇦","Qatar":"🇶🇦","Switzerland":"🇨🇭",
 "Brazil":"🇧🇷","Morocco":"🇲🇦","Haiti":"🇭🇹","Scotland":"🏴󠁧󠁢󠁳󠁣󠁴󠁿",
 "United States":"🇺🇸","Paraguay":"🇵🇾","Australia":"🇦🇺","Turkey":"🇹🇷",
 "Germany":"🇩🇪","Curaçao":"🇨🇼","Ivory Coast":"🇨🇮","Ecuador":"🇪🇨",
 "Netherlands":"🇳🇱","Japan":"🇯🇵","Sweden":"🇸🇪","Tunisia":"🇹🇳",
 "Belgium":"🇧🇪","Egypt":"🇪🇬","Iran":"🇮🇷","New Zealand":"🇳🇿",
 "Spain":"🇪🇸","Cape Verde":"🇨🇻","Saudi Arabia":"🇸🇦","Uruguay":"🇺🇾",
 "France":"🇫🇷","Senegal":"🇸🇳","Iraq":"🇮🇶","Norway":"🇳🇴",
 "Argentina":"🇦🇷","Algeria":"🇩🇿","Austria":"🇦🇹","Jordan":"🇯🇴",
 "Portugal":"🇵🇹","DR Congo":"🇨🇩","Uzbekistan":"🇺🇿","Colombia":"🇨🇴",
 "England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Croatia":"🇭🇷","Ghana":"🇬🇭","Panama":"🇵🇦"}

groups = {}
for g in "ABCDEFGHIJKL":
    order = [br["standings"][g][str(i)] for i in (1, 2, 3, 4)]
    rows = []
    for t in order:
        r = tp[tp["team"] == t].iloc[0]
        rows.append({"team": t, "p1": round(r["p_win_group"], 4),
                     "p2": round(r["p_group_2nd"], 4),
                     "adv": round(r["p_reach_r32"], 4),
                     "pts": round(r["exp_group_points"], 2)})
    groups[g] = rows

ko = pd.read_csv("data/kickoffs_ko.csv")
ko_times = {str(int(r.match)): {"utc": et_to_utc(r.date, r.et, r.city), "city": r.city}
            for r in ko.itertuples()}

DATA = {
 "flags": FLAGS, "n_sims": ss["n_sims"], "ko_times": ko_times,
 "top10": ss["champion_top10"], "finals": ss["top_finals"][:5],
 "bracket": br, "groups": groups,
 "matches": mp.fillna("").to_dict("records"),
 "teams": tp.round(4).to_dict("records"),
 "validation": {y: bt[y] for y in ("2014", "2018", "2022")},
 "best": bt["best"], "home_adv": round(ss["dc_home_adv"], 3), "rho": round(ss["dc_rho"], 4),
}

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Cup 26 — Statistical Forecast</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='t' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%2300854d'/%3E%3Cstop offset='.52' stop-color='%231e6fd9'/%3E%3Cstop offset='1' stop-color='%23d92d2d'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='64' height='64' rx='15' fill='url(%23t)'/%3E%3Ctext x='32' y='44' font-family='-apple-system,Helvetica,Arial' font-size='32' font-weight='800' font-style='italic' fill='white' text-anchor='middle'%3E26%3C/text%3E%3C/svg%3E">
<style>
:root{
 --bg:#f5f5f7; --surface:#ffffff; --txt:#1d1d1f; --mut:#6e6e73; --hair:#d2d2d7;
 --g1:#00854d; --g2:#1e6fd9; --g3:#d92d2d;            /* host tricolor: MEX · USA · CAN */
 --tri:linear-gradient(90deg,var(--g1),var(--g2) 52%,var(--g3));
 --blue:var(--g2); --blue-soft:rgba(30,111,217,.10); --green:#34c759; --red:#ff3b30;
 --track:#e8e8ed; --shadow:0 4px 24px rgba(0,0,0,.06), 0 1px 3px rgba(0,0,0,.04);
 --shadow-lg:0 12px 48px rgba(0,0,0,.10); --radius:18px;
 --nav-bg:rgba(251,251,253,.82); --tint:#fbfbfd;
}
@media (prefers-color-scheme: dark){
 :root{--bg:#000;--surface:#1c1c1e;--txt:#f5f5f7;--mut:#86868b;--hair:#38383a;
  --g1:#2fbf7f;--g2:#3f8cff;--g3:#ff5d5d;
  --blue:var(--g2);--blue-soft:rgba(63,140,255,.18);--track:#2c2c2e;
  --shadow:0 4px 24px rgba(0,0,0,.5);--shadow-lg:0 12px 48px rgba(0,0,0,.6);
  --nav-bg:rgba(22,22,23,.8);--tint:#101012}
 img.calib{filter:invert(.92) hue-rotate(180deg)}
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--txt);overflow-x:hidden;
 font:16px/1.6 -apple-system,BlinkMacSystemFont,"SF Pro Text","SF Pro Display","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
/* ---- nav ---- */
nav{position:sticky;top:0;z-index:100;background:var(--nav-bg);
 backdrop-filter:saturate(1.8) blur(20px);-webkit-backdrop-filter:saturate(1.8) blur(20px);
 border-bottom:1px solid rgba(0,0,0,.08)}
@media (prefers-color-scheme: dark){nav{border-bottom-color:rgba(255,255,255,.1)}}
nav .in{max-width:1100px;margin:0 auto;display:flex;align-items:center;gap:8px;
 padding:0 22px;height:48px;overflow-x:auto;scrollbar-width:none}
nav .in::-webkit-scrollbar{display:none}
nav b{display:flex;align-items:center;font-size:14px;font-weight:600;margin-right:auto;white-space:nowrap;letter-spacing:-.01em}
nav b span.tx{color:var(--mut);font-weight:500;margin-left:5px}
.lg{display:inline-flex;align-items:center;justify-content:center;width:27px;height:27px;border-radius:8px;
 background:var(--tri);color:#fff;font-weight:800;font-size:13px;letter-spacing:-.04em;margin-right:9px;
 box-shadow:0 2px 8px rgba(30,111,217,.35);font-style:italic}
nav a{color:var(--txt);opacity:.75;font-size:12.5px;padding:5px 12px;border-radius:999px;
 white-space:nowrap;font-weight:500;transition:.25s}
nav a:hover{opacity:1;text-decoration:none;background:var(--blue-soft)}
nav a.on{opacity:1;color:var(--blue);background:var(--blue-soft)}
nav a.livelink{opacity:1;color:#fff;background:var(--g3);font-weight:600}
nav a.livelink::before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:#fff;margin-right:5px;vertical-align:middle;animation:lp 1.6s infinite}
@keyframes lp{0%,100%{opacity:1}50%{opacity:.3}}
nav a.livelink:hover{color:#fff;background:var(--g3);filter:brightness(1.08)}
/* ---- layout ---- */
.wrap{max-width:1100px;margin:0 auto;padding:0 22px 110px}
section{margin-top:110px;scroll-margin-top:70px}
.shead{text-align:center;max-width:740px;margin:0 auto 44px}
.shead h2{font-size:clamp(30px,4.4vw,46px);font-weight:700;letter-spacing:-.022em;line-height:1.1}
.shead h2::after{content:"";display:block;width:58px;height:4.5px;border-radius:3px;background:var(--tri);margin:16px auto 0}
.shead p{color:var(--mut);font-size:18px;margin-top:14px;letter-spacing:-.01em}
/* ---- hero ---- */
header.hero{text-align:center;padding:104px 16px 0}
.eyebrow{display:inline-block;background:var(--tri);-webkit-background-clip:text;background-clip:text;
 color:transparent;font-weight:700;font-size:14px;letter-spacing:.02em}
.hero h1{font-size:clamp(42px,8vw,88px);font-weight:700;letter-spacing:-.03em;line-height:1.04;margin-top:10px}
.hero h1 .grad{background:var(--tri);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p.sub{color:var(--mut);font-size:clamp(17px,2.2vw,21px);max-width:680px;margin:22px auto 0;letter-spacing:-.012em}
.statrow{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;
 max-width:980px;margin:54px auto 0}
.stat{position:relative;overflow:hidden;background:var(--surface);border-radius:var(--radius);
 padding:28px 22px 26px;box-shadow:var(--shadow);transition:transform .35s cubic-bezier(.2,.8,.2,1)}
.stat::before{content:"";position:absolute;left:0;right:0;top:0;height:4px;background:var(--tri)}
.stat:hover{transform:translateY(-3px)}
.stat .v{font-size:30px;font-weight:700;letter-spacing:-.02em}
.stat .v em{font-style:normal;font-size:17px;color:var(--mut);font-weight:500}
.stat .k{color:var(--mut);font-size:13px;margin-top:6px}
.stat .t{font-weight:600;font-size:15px;margin-top:10px}
/* ---- bracket ---- */
.champ{display:flex;align-items:center;justify-content:center;gap:18px;text-align:left;
 border:2px solid transparent;border-radius:24px;box-shadow:var(--shadow-lg);
 background:linear-gradient(var(--surface),var(--surface)) padding-box,var(--tri) border-box;
 padding:30px 40px;max-width:620px;margin:0 auto 40px}
.champ .cup{font-size:44px}
.champ .t{font-size:32px;font-weight:700;letter-spacing:-.02em}
.champ .s{color:var(--mut);font-size:14px;margin-top:2px}
.bwrap{width:100vw;margin-left:calc(50% - 50vw);overflow-x:auto;padding:10px 0 18px;-webkit-overflow-scrolling:touch}
.bracket{display:flex;gap:12px;min-width:1280px;max-width:1440px;margin:0 auto;padding:0 22px;align-items:stretch}
.bcol{display:flex;flex-direction:column;flex:1;min-width:130px}
.bcol h4{text-align:center;color:var(--mut);font-size:10.5px;font-weight:600;
 text-transform:uppercase;letter-spacing:.08em;height:16px;margin-bottom:8px}
.ties{flex:1;display:flex;flex-direction:column;justify-content:space-around}
.ties .tie{margin:4px 0}
.tie{background:var(--surface);border-radius:12px;box-shadow:var(--shadow);overflow:hidden;font-size:12.5px}
.tie .mn{font-size:10px;color:var(--mut);padding:4px 10px 0;letter-spacing:.02em}
.tie .row{display:flex;align-items:center;gap:6px;padding:5px 10px}
.tie .row:last-child{padding-bottom:7px}
.tie .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--mut)}
.tie .pc{color:var(--mut);font-variant-numeric:tabular-nums;font-size:11.5px}
.tie .row.w .nm{font-weight:650;color:var(--txt)}
.tie .row.w .pc{color:var(--blue);font-weight:650}
.tie .row.w{background:var(--blue-soft)}
.finalcol .tie{box-shadow:var(--shadow-lg);border:2px solid transparent;
 background:linear-gradient(var(--surface),var(--surface)) padding-box,var(--tri) border-box}
.disclaimer{max-width:680px;margin:30px auto 0;text-align:center;color:var(--mut);font-size:14px;
 background:var(--surface);border-radius:999px;padding:12px 26px;box-shadow:var(--shadow)}
/* ---- groups ---- */
.ggrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}
.gcard{background:var(--surface);border-radius:var(--radius);padding:20px 22px;box-shadow:var(--shadow);
 transition:transform .35s cubic-bezier(.2,.8,.2,1)}
.gcard:hover{transform:translateY(-3px)}
.gcard h3{font-size:13px;font-weight:600;color:var(--mut);letter-spacing:.06em;margin-bottom:12px}
.grow{display:flex;align-items:center;gap:9px;padding:6px 0;font-size:14px}
.grow .pos{width:14px;color:var(--mut);font-weight:600;font-size:12px}
.grow .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:520}
.badge{font-size:10px;font-weight:600;border-radius:999px;padding:2.5px 9px;letter-spacing:.02em}
.badge.q{color:#fff;background:var(--g1)}
.badge.m{color:var(--blue);background:var(--blue-soft)}
.badge.o{color:var(--mut);background:var(--track)}
.bar{height:5px;border-radius:3px;background:var(--track);width:74px;overflow:hidden;flex:none}
.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--g1),var(--g2));border-radius:3px}
.grow .pv{width:40px;text-align:right;color:var(--mut);font-size:12px;font-variant-numeric:tabular-nums}
/* ---- controls + tables ---- */
.tzbar{display:flex;align-items:center;justify-content:center;gap:8px;margin:0 auto 18px;max-width:560px;
 background:var(--surface);border-radius:999px;padding:9px 18px;box-shadow:var(--shadow);
 color:var(--mut);font-size:13.5px;text-align:center}
.tzbar b{color:var(--txt);font-weight:600}
.tzbar .dot{width:7px;height:7px;border-radius:50%;background:var(--g1);flex:none}
.kc{white-space:nowrap}
.kc .kt{font-weight:600;font-variant-numeric:tabular-nums}
.kc .kd{display:block;color:var(--mut);font-size:11.5px}
.controls{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-bottom:26px}
.controls input,.controls select{background:var(--surface);border:1px solid var(--hair);color:var(--txt);
 border-radius:999px;padding:9px 18px;font-size:14px;font-family:inherit;outline:none;
 transition:border-color .2s, box-shadow .2s;-webkit-appearance:none;appearance:none}
.controls input:focus,.controls select:focus{border-color:var(--blue);box-shadow:0 0 0 3.5px var(--blue-soft)}
.controls input{min-width:220px}
.card{background:var(--surface);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden}
.tscroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:14px}
th{color:var(--mut);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;
 text-align:left;padding:14px 14px;border-bottom:1px solid var(--hair);white-space:nowrap;
 background:var(--surface)}
td{padding:12px 14px;border-bottom:1px solid var(--hair);vertical-align:middle}
tr:last-child td{border-bottom:none}
tr{transition:background .15s}
tbody tr:hover{background:var(--tint)}
.pbar{display:flex;height:6px;border-radius:3px;overflow:hidden;min-width:160px;background:var(--track)}
.pbar i{height:100%}.pbar .h{background:var(--g2)}.pbar .d{background:#aeaeb2}.pbar .a{background:var(--g3)}
.plab{display:flex;justify-content:space-between;font-size:11px;color:var(--mut);margin-top:5px;min-width:160px;font-variant-numeric:tabular-nums}
.fav{font-weight:650}
th.sort{cursor:pointer;user-select:none}
th.sort:hover{color:var(--txt)}
th.sort.on{color:var(--blue)}
.teamcell{display:flex;align-items:center;gap:8px;white-space:nowrap}
.sub{color:var(--mut);font-size:12px}
/* ---- model ---- */
.prose{max-width:760px;margin:0 auto;font-size:17px;letter-spacing:-.01em;color:var(--txt)}
.prose p{margin:16px 0}
.prose .mut{color:var(--mut)}
.vwrap{max-width:640px;margin:34px auto 0}
.vwrap td:nth-child(n+2),.vwrap th:nth-child(n+2){text-align:right;font-variant-numeric:tabular-nums}
.best{color:var(--green);font-weight:650}
img.calib{display:block;max-width:430px;width:100%;margin:34px auto 0;border-radius:var(--radius);box-shadow:var(--shadow)}
.dlrow{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:36px}
.btn{display:inline-block;border-radius:999px;padding:11px 24px;font-size:15px;font-weight:500;transition:.2s}
.btn.fill{background:var(--blue);color:#fff}
.btn.fill:hover{filter:brightness(1.08);text-decoration:none}
.btn.line{color:var(--blue);border:1px solid var(--blue)}
.btn.line:hover{background:var(--blue-soft);text-decoration:none}
footer{margin-top:110px;padding:28px 22px 0;border-top:1px solid var(--hair);
 color:var(--mut);font-size:12px;text-align:center;line-height:1.8}
/* ---- reveal ---- */
.rv{opacity:0;transform:translateY(22px);transition:opacity .7s ease,transform .7s cubic-bezier(.2,.8,.2,1)}
.rv.vis{opacity:1;transform:none}
@media (prefers-reduced-motion: reduce){.rv{opacity:1;transform:none;transition:none}html{scroll-behavior:auto}}
@media(max-width:700px){.champ{padding:22px;gap:12px}.champ .t{font-size:24px}.shead p{font-size:16px}}
</style>
</head>
<body>
<nav><div class="in"><b><span class="lg">26</span> World Cup 26 <span class="tx">· Forecast</span></b>
<a href="live.html" class="livelink">● Live</a>
<a href="#bracket">Bracket</a><a href="#groups">Groups</a><a href="#matches">Matches</a>
<a href="#teams">Odds</a><a href="#model">Model</a></div></nav>
<div class="wrap">

<header class="hero">
 <div class="eyebrow">CANADA · MEXICO · UNITED STATES — 200,000 SIMULATIONS, FROZEN PRE-TOURNAMENT</div>
 <h1>World Cup 26.<br><span class="grad">Forecast by the numbers.</span></h1>
 <p class="sub">A Dixon-Coles × Elo ensemble trained on 49,477 internationals since 1872, validated on the last
 three World Cups, and played through every one of the 104 matches — <b id="nsims"></b> times.</p>
 <div class="statrow" id="chips"></div>
</header>

<section id="bracket" class="rv">
 <div class="shead"><h2>The predicted bracket.</h2>
 <p>The single most likely path: modal group standings, FIFA's official Annex C third-place slotting,
 and the model's favourite advancing each tie. Percentages include extra time and penalties.</p></div>
 <div class="champ" id="champ"></div>
 <div class="bwrap"><div class="bracket" id="btree"></div></div>
 <div class="disclaimer">One bracket out of 200,000 futures — even the favourite lifts the trophy in only ~17% of them.</div>
</section>

<section id="groups" class="rv">
 <div class="shead"><h2>Group forecasts.</h2>
 <p>Predicted finishing order. Bars show each team's chance of surviving the group phase —
 the top two plus the eight best third-placed teams advance.</p></div>
 <div class="ggrid" id="ggrid"></div>
</section>

<section id="matches" class="rv">
 <div class="shead"><h2>Every match, quantified.</h2>
 <p>Win, draw and loss probabilities, expected goals and most likely scorelines for all 72 group fixtures — with kickoff times in your local zone.</p></div>
 <div class="tzbar" id="tzbar"></div>
 <div class="controls">
  <input id="q" type="search" placeholder="Search team…">
  <select id="gf"><option value="">All groups</option></select>
  <select id="df"><option value="">All dates</option></select>
 </div>
 <div class="card tscroll"><table id="mtable">
  <thead><tr><th>Kickoff</th><th>Grp</th><th>Fixture</th><th>H / D / A</th><th>xG</th><th>Most likely scores</th></tr></thead>
  <tbody></tbody></table></div>
</section>

<section id="teams" class="rv">
 <div class="shead"><h2>Title odds.</h2>
 <p>Advancement probabilities for all 48 teams, from the group phase to the trophy. Tap a column to sort.</p></div>
 <div class="card tscroll"><table id="ttable">
  <thead><tr>
   <th class="sort" data-k="team">Team</th><th class="sort" data-k="group">Grp</th>
   <th class="sort" data-k="elo">Elo</th><th class="sort" data-k="p_reach_r32">Advance</th>
   <th class="sort" data-k="p_reach_r16">R16</th><th class="sort" data-k="p_reach_qf">QF</th>
   <th class="sort" data-k="p_reach_sf">SF</th><th class="sort" data-k="p_reach_final">Final</th>
   <th class="sort on" data-k="p_champion">Champion</th>
  </tr></thead><tbody></tbody></table></div>
</section>

<section id="model" class="rv">
 <div class="shead"><h2>The model.</h2>
 <p>Two independent engines, blended and validated out-of-sample — no betting-market data, fully reproducible.</p></div>
 <div class="prose" id="prose"></div>
 <div class="vwrap card"><table id="vtable">
  <thead><tr><th>World Cup</th><th>Blend</th><th>Dixon-Coles</th><th>Elo</th><th>Uniform</th></tr></thead><tbody></tbody></table></div>
 <p style="text-align:center" class="sub">Three-way log loss on group-stage results, fitted strictly on pre-tournament data — lower is better.
 Hyperparameters tuned on 2014 + 2018; <b>2022 fully held out</b>.</p>
 <img class="calib" alt="Calibration plot" src="data:image/png;base64,__CALIB__">
 <div class="dlrow">
  <a class="btn fill" href="WC2026_report.docx">Full report (.docx)</a>
  <a class="btn line" href="WC2026_predictions.xlsx">Predictions workbook (.xlsx)</a>
 </div>
</section>

<footer>Generated 11 June 2026, pre-tournament · 200,000 simulations, seed 20260611<br>
Data: github.com/martj42/international_results · Bracket &amp; Annex C: FIFA regulations ·
Model: penalised Dixon-Coles (ξ = 0.4/yr) ⊗ World Football Elo, log-linear blend w = 0.4<br>
Unofficial fan analytics project — not affiliated with or endorsed by FIFA. Team names and flags are used for identification only.</footer>
</div>

<script>
const D = __DATA__;
const F = t => (D.flags[t]||"");
const pc = (x,d=0) => (100*x).toFixed(d)+"%";

/* time zone — localize all kickoffs to the visitor's own zone */
const TZ = Intl.DateTimeFormat().resolvedOptions().timeZone || "your time zone";
const tzAbbr = (()=>{ try{
 return new Intl.DateTimeFormat("en-US",{timeZoneName:"short"}).formatToParts(new Date())
   .find(p=>p.type==="timeZoneName").value; }catch(e){ return ""; } })();
const fmtTime = new Intl.DateTimeFormat(undefined,{hour:"numeric",minute:"2-digit"});
const fmtDay  = new Intl.DateTimeFormat(undefined,{weekday:"short",month:"short",day:"numeric"});
const fmtDayKey = new Intl.DateTimeFormat("en-CA",{year:"numeric",month:"2-digit",day:"2-digit"});
function localKO(utc){ const dt=new Date(utc);
 return {time:fmtTime.format(dt), day:fmtDay.format(dt), key:fmtDayKey.format(dt), dt}; }

/* hero */
document.getElementById("nsims").textContent = D.n_sims.toLocaleString();
const t1 = D.top10[0], t2 = D.top10[1], fin = D.finals[0];
document.getElementById("chips").innerHTML = [
 [pc(t1.p_champion,1), "Title favourite", F(t1.team)+" "+t1.team],
 [pc(t2.p_champion,1), "Second favourite", F(t2.team)+" "+t2.team],
 [pc(fin.p,1)+" <em>of sims</em>", "Most likely final", fin.final.replace(" vs "," – ")],
 [D.validation["2022"].blend.log_loss.toFixed(3)+" <em>log loss</em>", "Held-out 2022 (uniform 1.099)", "Beats both components"],
].map(c=>`<div class="stat"><div class="v">${c[0]}</div><div class="k">${c[1]}</div><div class="t">${c[2]}</div></div>`).join("");

/* bracket */
const byM = {}; for (const r of ["r32","r16","qf","sf","final"]) for (const m of D.bracket.rounds[r]) byM[m.m]=m;
const cols = [
 ["Round of 32",[74,77,73,75,83,84,81,82]], ["Round of 16",[89,90,93,94]], ["Quarterfinals",[97,98]], ["Semifinal",[101]],
 ["Final",[104]],
 ["Semifinal",[102]], ["Quarterfinals",[99,100]], ["Round of 16",[91,92,95,96]], ["Round of 32",[76,78,79,80,86,88,85,87]]
];
function tie(m){
 const rows = [[m.t1,m.p1],[m.t2,1-m.p1]];
 const kt = D.ko_times[m.m];
 let meta = `M${m.m} · ${m.venue}`;
 if (kt){ const lp = localKO(kt.utc); meta = `M${m.m} · ${lp.day}, ${lp.time} · ${kt.city}`; }
 return `<div class="tie"><div class="mn">${meta}</div>` + rows.map(([t,p])=>
  `<div class="row ${t===m.winner?"w":""}"><span>${F(t)}</span><span class="nm">${t}</span><span class="pc">${pc(p)}</span></div>`).join("") + `</div>`;
}
document.getElementById("btree").innerHTML = cols.map(([h,ms])=>
 `<div class="bcol ${ms[0]===104?"finalcol":""}"><h4>${h}</h4><div class="ties">`+ms.map(n=>tie(byM[n])).join("")+`</div></div>`).join("");
const ch = D.bracket.champion;
document.getElementById("champ").innerHTML =
 `<span class="cup">🏆</span><div><div class="t">${F(ch)} ${ch}</div>
  <div class="s">Predicted champion — wins ${pc(D.top10.find(x=>x.team===ch).p_champion,1)} of all simulations</div></div>`;

/* groups */
const qset = new Set(D.bracket.qualified_third_groups);
document.getElementById("ggrid").innerHTML = Object.entries(D.groups).map(([g,rows])=>
 `<div class="gcard"><h3>GROUP ${g}</h3>`+rows.map((r,i)=>{
   const badge = i<2 ? `<span class="badge q">ADV</span>` :
     (i===2 ? (qset.has(g) ? `<span class="badge m">3rd ✓</span>` : `<span class="badge o">3rd</span>`) : `<span class="badge o" style="opacity:.55">OUT</span>`);
   return `<div class="grow"><span class="pos">${i+1}</span><span>${F(r.team)}</span><span class="nm">${r.team}</span>
    ${badge}<span class="bar"><i style="width:${100*r.adv}%"></i></span><span class="pv">${pc(r.adv)}</span></div>`;
  }).join("")+`</div>`).join("");

/* matches — kickoff times localized to the visitor's own time zone */
function localParts(m){ return m.utc_kickoff ? localKO(m.utc_kickoff) : null; }
document.getElementById("tzbar").innerHTML =
 `<span class="dot"></span>Kickoff times shown in <b>your local time</b> — detected as <b>${TZ.replace(/_/g," ")}${tzAbbr?` (${tzAbbr})`:""}</b>.`;

const mt = document.querySelector("#mtable tbody");
const gf = document.getElementById("gf"), df = document.getElementById("df"), q = document.getElementById("q");
[...new Set(D.matches.map(m=>m.group))].sort().forEach(g=>gf.insertAdjacentHTML("beforeend",`<option>${g}</option>`));
// date dropdown uses the visitor's LOCAL calendar dates
const localDays = [...new Map(D.matches.map(m=>{const lp=localParts(m);return lp?[lp.key,lp.day]:["",""];}).filter(x=>x[0])).entries()].sort();
localDays.forEach(([key,lab])=>df.insertAdjacentHTML("beforeend",`<option value="${key}">${lab}</option>`));
function renderMatches(){
 const s = q.value.toLowerCase(), g = gf.value, d = df.value;
 mt.innerHTML = D.matches.filter(m =>{
   const lp = localParts(m);
   return (!g || m.group===g) && (!d || (lp && lp.key===d)) &&
   (!s || m.home_team.toLowerCase().includes(s) || m.away_team.toLowerCase().includes(s));})
  .map(m=>{
   const fav = m.p_home_win>=m.p_away_win && m.p_home_win>=m.p_draw ? "h" : (m.p_away_win>=m.p_draw ? "a":"d");
   const lp = localParts(m);
   const kc = lp ? `<div class="kc"><span class="kt">${lp.time}</span><span class="kd">${lp.day}</span></div>`
                 : `<div class="kc sub">${m.date.slice(5)}</div>`;
   return `<tr><td>${kc}</td><td>${m.group}</td>
   <td><div class="teamcell"><span class="${fav==="h"?"fav":""}">${F(m.home_team)} ${m.home_team}</span>
    <span class="sub">v</span><span class="${fav==="a"?"fav":""}">${F(m.away_team)} ${m.away_team}</span></div>
    <div class="sub">${m.city}</div></td>
   <td><div class="pbar"><i class="h" style="width:${100*m.p_home_win}%"></i><i class="d" style="width:${100*m.p_draw}%"></i><i class="a" style="width:${100*m.p_away_win}%"></i></div>
    <div class="plab"><span>${pc(m.p_home_win)}</span><span>${pc(m.p_draw)}</span><span>${pc(m.p_away_win)}</span></div></td>
   <td style="white-space:nowrap">${m.exp_goals_home.toFixed(2)} – ${m.exp_goals_away.toFixed(2)}</td>
   <td class="sub" style="font-size:13px">${m.most_likely_scores}</td></tr>`;}).join("");
}
[q,gf,df].forEach(el=>el.addEventListener("input",renderMatches)); renderMatches();

/* teams */
let sortK = "p_champion", sortAsc = false;
const tt = document.querySelector("#ttable tbody");
function renderTeams(){
 const rows = [...D.teams].sort((a,b)=>{
  const va=a[sortK], vb=b[sortK];
  return (typeof va==="string" ? va.localeCompare(vb) : va-vb) * (sortAsc?1:-1);});
 tt.innerHTML = rows.map(r=>`<tr>
  <td><div class="teamcell">${F(r.team)} ${r.team}</div></td><td>${r.group}</td><td>${Math.round(r.elo)}</td>
  <td>${pc(r.p_reach_r32)}</td><td>${pc(r.p_reach_r16)}</td><td>${pc(r.p_reach_qf)}</td>
  <td>${pc(r.p_reach_sf)}</td><td>${pc(r.p_reach_final,1)}</td>
  <td><div class="teamcell"><span class="bar" style="width:64px"><i style="width:${Math.min(100,100*r.p_champion/0.20)}%"></i></span>
   <b style="font-variant-numeric:tabular-nums">${pc(r.p_champion,1)}</b></div></td></tr>`).join("");
 document.querySelectorAll("#ttable th.sort").forEach(th=>th.classList.toggle("on", th.dataset.k===sortK));
}
document.querySelectorAll("#ttable th.sort").forEach(th=>th.addEventListener("click",()=>{
 const k = th.dataset.k; if (k===sortK) sortAsc=!sortAsc; else {sortK=k; sortAsc = (k==="team"||k==="group");}
 renderTeams();}));
renderTeams();

/* model prose */
document.getElementById("prose").innerHTML = `
<p><b>Two engines, one forecast.</b> Goal rates for every fixture come from a ${Math.round(D.best.blend_w*100)}/${Math.round((1-D.best.blend_w)*100)} log-linear blend of
(1) a <b>time-decayed Dixon-Coles bivariate Poisson</b> — attack and defence strengths per team, a fitted
home advantage of ${D.home_adv} log-goals applied only to hosts playing at home, a low-score dependence
correction (ρ = ${D.rho}), exponential decay ξ = ${D.best.xi}/yr and importance-weighted matches
(friendlies × ${D.best.friendly_w}), estimated by penalised maximum likelihood — and
(2) <b>World Football Elo</b> ratings over all 154 years, converted to goal rates through leakage-free
Poisson regressions fitted on stored pre-match ratings.</p>
<p><b>Tournament engine.</b> Group scorelines are sampled from each fixture's exact τ-corrected score grid,
standings apply FIFA tiebreakers (points, GD, GF, head-to-head, then randomised conduct/ranking proxies),
the best eight thirds are slotted via FIFA's official 495-row Annex C table, and knockouts get extra time
(⅓-intensity Poisson) plus 50/50 shootouts, with venue-aware host advantage — Estadio Azteca through the
round of 16 for Mexico, Vancouver for Canada's group winner, and near-everything on home soil for the US.</p>
<p class="mut"><b>Honest limitations.</b> Team-level only (no injuries or squads), no betting-market input,
hyperparameters tuned on just two tournaments, shootouts as coin flips, and a never-before-played 48-team
format. Treat probabilities as calibrated estimates, not certainties.</p>`;

/* validation table */
document.querySelector("#vtable tbody").innerHTML = ["2014","2018","2022"].map(y=>{
 const v = D.validation[y];
 const best = Math.min(v.blend.log_loss, v.dc_only.log_loss, v.elo_only.log_loss, v.uniform.log_loss);
 const td = x => `<td class="${x===best?'best':''}">${x.toFixed(3)}</td>`;
 return `<tr><td>${y}${y==="2022"?" (holdout)":""}</td>${td(v.blend.log_loss)}${td(v.dc_only.log_loss)}${td(v.elo_only.log_loss)}${td(v.uniform.log_loss)}</tr>`;
}).join("");

/* nav highlight + scroll reveal */
const secs=[...document.querySelectorAll("section")], links=[...document.querySelectorAll("nav a")];
addEventListener("scroll",()=>{let cur="";
 for(const s of secs) if (scrollY >= s.offsetTop-140) cur=s.id;
 links.forEach(l=>l.classList.toggle("on", l.getAttribute("href")==="#"+cur));},{passive:true});
if ("IntersectionObserver" in window){
 const io = new IntersectionObserver(es=>es.forEach(e=>{ if(e.isIntersecting){e.target.classList.add("vis"); io.unobserve(e.target);} }),{threshold:.08});
 document.querySelectorAll(".rv").forEach(el=>io.observe(el));
} else {
 document.querySelectorAll(".rv").forEach(el=>el.classList.add("vis"));
}
</script>
</body>
</html>"""

html = HTML.replace("__DATA__", json.dumps(DATA, ensure_ascii=False)).replace("__CALIB__", calib_b64)
import os
os.makedirs("website", exist_ok=True)
open("website/index.html", "w", encoding="utf-8").write(html)
# copy downloadable deliverables into the site folder so links work on any host
import shutil
for fn in ("WC2026_report.docx", "WC2026_predictions.xlsx"):
    src = os.path.join("output", fn)
    if os.path.exists(src):
        shutil.copy(src, os.path.join("website", fn))
print(f"website/index.html written ({len(html)/1024:.0f} KB)")
