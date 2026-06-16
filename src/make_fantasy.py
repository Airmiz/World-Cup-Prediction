"""Generate website/fantasy.html — the World Cup 2026 Fantasy game.

Self-contained app (HTML/CSS/JS). Fetches data/fantasy.json (player DB + per-gameweek
points, refreshed every 2h) at runtime; the squad, captain and bench are saved in the
browser (localStorage). Scoring, auto-subs, captaincy, the dream-team ceiling and a
percentile rank are all computed client-side.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from make_site import FLAGS

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Cup 26 — Fantasy</title>
<meta name="theme-color" content="#f5f5f7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<meta name="description" content="World Cup 2026 Fantasy — pick a 15-player squad under a budget, captain your star, and score from real match data every matchday.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<meta property="og:type" content="website">
<meta property="og:title" content="World Cup 2026 — Fantasy">
<meta property="og:description" content="Build your squad, captain your star, and climb the table — scored from real World Cup match data.">
<meta property="og:image" content="https://airmiz.github.io/World-Cup-Prediction/og.png">
<meta property="og:url" content="https://airmiz.github.io/World-Cup-Prediction/fantasy.html">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://airmiz.github.io/World-Cup-Prediction/og.png">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='15' fill='%2334c759'/%3E%3Ctext x='32' y='44' font-family='Arial' font-size='30' font-weight='800' fill='white' text-anchor='middle'%3EF%3C/text%3E%3C/svg%3E">
<style>
:root{--bg:#f5f5f7;--surface:#fff;--card:#fff;--txt:#1d1d1f;--mut:#6e6e73;--border:#e3e3e8;--track:#ececf0;
 --blue:#1e6fd9;--blue-soft:rgba(30,111,217,.1);--live:#34c759;--amber:#ff9f0a;--red:#ff3b30;--shadow:0 1px 3px rgba(0,0,0,.07);
 --pitch1:#2ea14d;--pitch2:#249a45;--gold:#ffcf33}
@media (prefers-color-scheme: dark){:root{--bg:#000;--surface:#121214;--card:#1c1c1f;--txt:#f5f5f7;--mut:#98989f;--border:#2a2a30;--track:#26262b;--blue:#4d9bff;--blue-soft:rgba(77,155,255,.14);--shadow:0 1px 3px rgba(0,0,0,.5)}}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--txt);-webkit-font-smoothing:antialiased}
a{color:inherit}
nav{position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--bg) 86%,transparent);backdrop-filter:saturate(180%) blur(18px);border-bottom:1px solid var(--border)}
nav .in{max-width:1080px;margin:0 auto;padding:11px 18px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
nav b{font-weight:800;letter-spacing:-.02em;margin-right:6px}
nav .lg{display:inline-flex;width:24px;height:24px;border-radius:7px;background:linear-gradient(135deg,#1f9d4d,#34c759);color:#fff;align-items:center;justify-content:center;font-size:12px;font-weight:800;font-style:italic;margin-right:7px}
nav a{color:var(--mut);text-decoration:none;font-size:14px;font-weight:600}
nav a.on,nav a:hover{color:var(--txt)}
.wrap{max-width:1080px;margin:0 auto;padding:18px}
.hero{padding:14px 4px 6px}
.hero h1{font-size:clamp(26px,5vw,40px);letter-spacing:-.03em;margin:.1em 0}
.hero .grad{background:linear-gradient(120deg,#1f9d4d,#34c759 60%,#1e6fd9);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:var(--mut);max-width:60ch;margin:.2em 0 0}
/* top bar: budget / points / gw */
.bar{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}
.bcard{background:var(--surface);border-radius:14px;box-shadow:var(--shadow);padding:13px 16px}
.bcard .bv{font-size:25px;font-weight:900;line-height:1;font-variant-numeric:tabular-nums}
.bcard .bl{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--mut);margin-top:5px}
.bcard .bs{font-size:11px;color:var(--mut);margin-top:2px}
.budbar{height:6px;background:var(--track);border-radius:3px;margin-top:8px;overflow:hidden}
.budbar i{display:block;height:100%;background:var(--live);border-radius:3px;transition:width .3s,background .3s}
.budbar i.over{background:var(--red)}
.tabs{display:flex;gap:6px;margin:6px 0 14px;flex-wrap:wrap}
.tab{padding:8px 15px;border-radius:999px;border:1px solid var(--border);background:var(--surface);color:var(--mut);font-weight:700;font-size:13px;cursor:pointer}
.tab.on{background:var(--txt);color:var(--bg);border-color:var(--txt)}
.btn{padding:8px 14px;border-radius:10px;border:1px solid var(--border);background:var(--surface);color:var(--txt);font-weight:700;font-size:13px;cursor:pointer}
.btn:hover{border-color:var(--blue)}
.btn.solid{background:var(--blue);color:#fff;border-color:var(--blue)}
.btn.live{background:var(--live);color:#fff;border-color:var(--live)}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.sec{display:none}.sec.on{display:block}
/* pitch */
.field{background:linear-gradient(180deg,var(--pitch1),var(--pitch2));border-radius:18px;padding:16px 8px 10px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.field::before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(180deg,rgba(255,255,255,.05) 0 38px,transparent 38px 76px);pointer-events:none}
.line{display:flex;justify-content:center;gap:clamp(4px,2.5vw,26px);margin:8px 0;position:relative;z-index:1;flex-wrap:wrap}
.slot{width:74px;text-align:center;cursor:pointer;user-select:none}
.jersey{width:46px;height:46px;margin:0 auto;border-radius:50%;background:rgba(255,255,255,.92);display:flex;align-items:center;justify-content:center;font-weight:800;color:#1b6;box-shadow:0 2px 6px rgba(0,0,0,.25);position:relative;font-size:13px;border:2px solid rgba(255,255,255,.6)}
.jersey.empty{background:rgba(255,255,255,.16);border:2px dashed rgba(255,255,255,.5);color:#fff}
.jersey .cap{position:absolute;top:-6px;right:-6px;width:20px;height:20px;border-radius:50%;background:var(--txt);color:var(--bg);font-size:11px;display:flex;align-items:center;justify-content:center;font-weight:900;border:2px solid #fff}
.jersey .cap.v{background:#fff;color:var(--txt)}
.snm{font-size:11px;font-weight:700;color:#fff;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-shadow:0 1px 2px rgba(0,0,0,.4)}
.spt{display:inline-block;font-size:10.5px;font-weight:800;color:#06301a;background:#fff;border-radius:5px;padding:1px 6px;margin-top:2px;min-width:30px}
.spt.fx{background:rgba(255,255,255,.25);color:#fff}
.benchwrap{margin-top:10px;background:var(--surface);border-radius:14px;box-shadow:var(--shadow);padding:10px 8px}
.benchh{font-size:11px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--mut);text-align:center;margin-bottom:6px}
.bench{display:flex;justify-content:center;gap:clamp(4px,3vw,24px);flex-wrap:wrap}
.jersey.phead{background-size:cover;background-position:50% 16%;background-repeat:no-repeat;background-color:rgba(255,255,255,.92)}
.jersey .pnum{line-height:1}
.jersey.has-img .pnum{display:none}
.jersey.has-img{color:transparent;border-color:#fff}
.mchip{display:inline-flex;align-items:center;gap:5px;margin:3px 10px 3px 0;font-size:12.5px;font-weight:600;white-space:nowrap}
.mhead{width:26px;height:26px;border-radius:50%;background:var(--track) no-repeat center 16%;background-size:cover;border:1px solid var(--border);display:inline-block;flex:none}
.bench .jersey{background:var(--track);color:var(--mut)}
.bench .jersey.has-img{background-color:var(--track)}
.bench .jersey.empty{background:var(--track);border:2px dashed var(--border)}
.bench .snm{color:var(--txt)}
.bench .spt{background:var(--blue-soft);color:var(--blue)}
/* picker modal */
.ov{position:fixed;inset:0;background:rgba(0,0,0,.5);display:none;z-index:60;align-items:flex-end;justify-content:center}
.ov.show{display:flex}
@media(min-width:640px){.ov{align-items:center}}
.sheet{background:var(--bg);width:100%;max-width:620px;max-height:90vh;border-radius:18px 18px 0 0;overflow:hidden;display:flex;flex-direction:column}
@media(min-width:640px){.sheet{border-radius:18px}}
#pickov{z-index:70}
.budtog{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:700;color:var(--mut);cursor:pointer;user-select:none}
.budtog input{width:16px;height:16px;accent-color:var(--blue);cursor:pointer}
.dboard{display:flex;gap:6px;flex-wrap:wrap;padding:12px 16px 4px}
.dchip{display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 9px;border-radius:10px;background:var(--surface);border:1px solid var(--border);font-size:11px;font-weight:700;min-width:52px;text-align:center}
.dchip .dn{font-size:10px;color:var(--mut);font-weight:600;white-space:nowrap;max-width:72px;overflow:hidden;text-overflow:ellipsis}
.dchip.onclock{border-color:var(--blue);background:var(--blue-soft);box-shadow:0 0 0 2px var(--blue-soft)}
.dchip.mechip{border-color:var(--live)}
.dchip .dc{font-size:14px;font-weight:900}
.dstatus{padding:8px 16px;font-size:13.5px;font-weight:700;text-align:center}
.dstatus .gobtn{margin-top:7px}
.dlog{overflow-y:auto;padding:4px 16px 16px;display:flex;flex-direction:column;gap:4px}
.dlogrow{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:5px 9px;border-radius:8px;background:var(--surface)}
.dlogrow.mine{background:var(--blue-soft)}
.dlogrow .rr{color:var(--mut);font-weight:700;font-size:11px;min-width:42px}
.dlogrow .pp{width:24px;height:24px;border-radius:50%;background:var(--track) no-repeat center 16%;background-size:cover;border:1px solid var(--border);flex:none}
.sheeth{padding:14px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px}
.sheeth b{font-size:16px}
.sheeth .x{margin-left:auto;background:none;border:none;color:var(--mut);font-size:22px;cursor:pointer}
.filt{padding:10px 16px;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid var(--border)}
.filt input,.filt select{padding:7px 10px;border-radius:9px;border:1px solid var(--border);background:var(--surface);color:var(--txt);font-size:13px}
.filt input{flex:1;min-width:120px}
.plist{overflow:auto;flex:1}
.pl{display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center;padding:10px 16px;border-bottom:1px solid var(--border);cursor:pointer}
.pl:hover{background:var(--surface)}
.pl.dis{opacity:.4;cursor:not-allowed}
.pl .pnm{font-weight:700}
.pl .psub{font-size:11.5px;color:var(--mut)}
.pl .ppr{font-weight:800;font-variant-numeric:tabular-nums;text-align:right}
.pl .ppt{font-size:11px;color:var(--mut);text-align:right}
.pos-tag{display:inline-block;font-size:9.5px;font-weight:800;border-radius:5px;padding:1px 5px;color:#fff;margin-right:5px}
.pos-GK{background:#e0a800}.pos-DEF{background:#1f9d4d}.pos-MID{background:#1e6fd9}.pos-FWD{background:#d9385f}
/* table */
.tbl{width:100%;border-collapse:collapse;background:var(--surface);border-radius:14px;overflow:hidden;box-shadow:var(--shadow);font-size:13.5px}
.tbl th,.tbl td{padding:9px 11px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap}
.tbl th{font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:var(--mut);cursor:pointer;user-select:none}
.tbl td.n{text-align:right;font-variant-numeric:tabular-nums}
.tbl tr:hover td{background:var(--bg)}
.tscroll{overflow-x:auto}
/* gameweek + compete */
.gwrow{display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center;padding:11px 14px;border-bottom:1px solid var(--border)}
.gwrow .gwn{font-weight:700}.gwrow .gwsub{font-size:11.5px;color:var(--mut)}
.gwrow .gwp{font-size:20px;font-weight:900;font-variant-numeric:tabular-nums}
.card{background:var(--surface);border-radius:14px;box-shadow:var(--shadow);padding:4px 0;margin-bottom:14px}
.card h3{font-size:13px;font-weight:800;padding:13px 16px 4px;margin:0}
.cmp{display:grid;grid-template-columns:1fr 70px;gap:8px;align-items:center;padding:9px 16px}
.cmp .cbar{height:9px;background:var(--track);border-radius:5px;overflow:hidden}
.cmp .cbar i{display:block;height:100%;border-radius:5px}
.cmp .cv{text-align:right;font-weight:800;font-variant-numeric:tabular-nums}
.hint{font-size:12.5px;color:var(--mut);padding:4px 16px 14px}
.empty{padding:40px 16px;text-align:center;color:var(--mut)}
footer{max-width:1080px;margin:10px auto 30px;padding:0 18px;color:var(--mut);font-size:12px;line-height:1.7}
.toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(20px);background:var(--txt);color:var(--bg);padding:11px 18px;border-radius:12px;font-weight:600;opacity:0;pointer-events:none;transition:.25s;z-index:80}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
@media (prefers-reduced-motion: reduce){*{transition:none!important;animation:none!important}}
</style>
</head>
<body>
<nav><div class="in"><b><span class="lg">26</span>WC Fantasy</b>
<a href="index.html">Forecast</a><a href="live.html">Live</a><a href="fantasy.html" class="on">Fantasy</a></div></nav>
<div class="wrap">
 <header class="hero">
  <h1>Build your <span class="grad">World Cup XI.</span></h1>
  <p>Draft 15 players against 5 AI managers — <b>once a player is drafted he's off the board for everyone</b>. Run a live snake draft or auto-draft, captain your star for double points, and score from real match data every matchday. Your squad saves to this device.</p>
 </header>
 <div class="bar" id="bar"></div>
 <div class="row" style="margin-bottom:8px">
  <button class="btn solid" id="livedraft">🎯 Live draft</button>
  <button class="btn" id="autodraft">⚡ Auto-draft my team</button>
  <button class="btn" id="reset">Reset</button>
  <button class="btn" id="share">🔗 Share</button>
  <label class="budtog" title="Salary cap on or off"><input type="checkbox" id="budtoggle" checked><span>£100 cap</span></label>
  <span id="valid" style="font-size:12.5px;color:var(--mut)"></span>
 </div>
 <div class="tabs">
  <div class="tab on" data-sec="team">My Team</div>
  <div class="tab" data-sec="players">Players</div>
  <div class="tab" data-sec="points">Points &amp; Rank</div>
 </div>

 <section class="sec on" id="sec-team">
  <div class="field" id="pitch"></div>
  <div class="benchwrap"><div class="benchh">Substitutes' bench — auto-subbed in if a starter doesn't play</div><div class="bench" id="bench"></div></div>
  <div class="hint">Tap a slot to pick or change a player. Tap a starter to make them <b>captain</b> (C = double points, second tap = vice). Drag isn't needed — bench order decides auto-subs.</div>
 </section>

 <section class="sec" id="sec-players">
  <div class="row" style="margin-bottom:10px">
   <input id="psearch" placeholder="Search players…" style="flex:1;min-width:140px;padding:8px 11px;border-radius:9px;border:1px solid var(--border);background:var(--surface);color:var(--txt)">
   <select id="pposf" style="padding:8px;border-radius:9px;border:1px solid var(--border);background:var(--surface);color:var(--txt)"><option value="">All positions</option><option>GK</option><option>DEF</option><option>MID</option><option>FWD</option></select>
  </div>
  <div class="tscroll"><table class="tbl" id="ptbl"></table></div>
 </section>

 <section class="sec" id="sec-points">
  <div id="ptsbox"></div>
 </section>
</div>

<div class="ov" id="draftov"><div class="sheet">
 <div class="sheeth"><b id="draftttl">🎯 Live Draft</b><button class="x" id="draftx">✕</button></div>
 <div id="draftboard" class="dboard"></div>
 <div id="draftstatus" class="dstatus"></div>
 <div class="dlog" id="draftlog"></div>
</div></div>
<div class="ov" id="pickov"><div class="sheet">
 <div class="sheeth"><b id="pickttl">Pick a player</b><button class="x" id="pickx">✕</button></div>
 <div class="filt"><input id="fsearch" placeholder="Search…"><select id="fteam"><option value="">All teams</option></select><select id="fsort"><option value="proj">Sort: projected</option><option value="form">Sort: form (MD1)</option><option value="price">Sort: price</option><option value="value">Sort: value</option></select></div>
 <div class="plist" id="plist"></div>
</div></div>
<div class="ov" id="mgrov"><div class="sheet">
 <div class="sheeth"><b id="mgrname">Manager</b><button class="x" id="mgrx">✕</button></div>
 <div class="plist" id="mgrbody"></div>
</div></div>
<div class="toast" id="toast"></div>

<footer>
 Fantasy scoring (FPL-style): appearance 1pt (2 if 60’+), goal GK/DEF 6 · MID 5 · FWD 4, assist 3, clean sheet GK/DEF 4 · MID 1, 3 saves 1pt, −1 per 2 conceded (GK/DEF), yellow −1, red −3, own goal −2, plus up to 3 match bonus. Captain scores double. Points settle from real match data, refreshed through the tournament.<br>
 Squads via openfootball · player events &amp; stats via ESPN · prices model-derived. Unofficial fan project, not affiliated with FIFA.
</footer>

<script>
const FLAGS=__FLAGS__;
const F={budget:100,squad:{GK:2,DEF:5,MID:5,FWD:3},max:3,players:[],byId:{},gws:[]};
const POS=["GK","DEF","MID","FWD"]; const FORM_MIN={GK:1,DEF:3,MID:2,FWD:1}, FORM_MAX={GK:1,DEF:5,MID:5,FWD:3};
const flag=t=>FLAGS[t]||"🏳️";
const $=s=>document.querySelector(s);
let S={picks:[],cap:null,vice:null,bench:[]};   // picks = all 15 ids; bench = 4 ids (rest are XI)
let pickFor=null;   // {pos, slotIndex} when picker open

function load(){ try{const v=JSON.parse(localStorage.getItem("wcfantasy")); if(v&&v.picks)S=v;}catch(e){}
  const u=new URLSearchParams(location.search).get("t"); if(u){ try{ const ids=u.split(".").filter(Boolean); if(ids.length>=11){ S={picks:ids.slice(0,15),cap:ids[15]||null,vice:ids[16]||null,bench:ids.slice(11,15)}; } }catch(e){} } }
function save(){ localStorage.setItem("wcfantasy",JSON.stringify(S)); }
function toast(m){ const t=$("#toast"); t.textContent=m; t.classList.add("show"); clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove("show"),1800); }

// ---------- squad helpers ----------
function picked(){ return S.picks.map(id=>F.byId[id]).filter(Boolean); }
function spent(){ return picked().reduce((s,p)=>s+p.price,0); }
function teamCount(team){ return picked().filter(p=>p.team===team).length; }
function posCount(ids){ const c={GK:0,DEF:0,MID:0,FWD:0}; ids.map(id=>F.byId[id]).filter(Boolean).forEach(p=>c[p.pos]++); return c; }
function xiIds(){ return S.picks.filter(id=>!S.bench.includes(id)); }
function benchIds(){ return S.bench.slice(); }

// ensure picks split into a legal XI + 4 bench (auto: best by pts, valid formation)
function normaliseXI(){
  const ps=picked(); if(ps.length<15){ S.bench=S.picks.filter(id=>!xiIds().includes(id)); return; }
  // choose XI maximising pts within formation limits; keep 1 GK
  const byPos={GK:[],DEF:[],MID:[],FWD:[]}; ps.forEach(p=>byPos[p.pos].push(p));
  for(const k in byPos) byPos[k].sort((a,b)=>MET(b)-MET(a)||b.price-a.price);
  const xi=[byPos.GK[0]];
  let need=10; const take={DEF:FORM_MIN.DEF,MID:FORM_MIN.MID,FWD:FORM_MIN.FWD};
  ["DEF","MID","FWD"].forEach(k=>{ for(let i=0;i<take[k];i++){ if(byPos[k][i]){xi.push(byPos[k][i]);need--;} } });
  // fill remaining best outfielders respecting max
  const pool=[].concat(byPos.DEF.slice(FORM_MIN.DEF),byPos.MID.slice(FORM_MIN.MID),byPos.FWD.slice(FORM_MIN.FWD)).sort((a,b)=>MET(b)-MET(a)||b.price-a.price);
  const cnt={GK:1,DEF:FORM_MIN.DEF,MID:FORM_MIN.MID,FWD:FORM_MIN.FWD};
  for(const p of pool){ if(need<=0)break; if(cnt[p.pos]<FORM_MAX[p.pos]){ xi.push(p); cnt[p.pos]++; need--; } }
  const xiset=new Set(xi.map(p=>p.id));
  S.bench=ps.filter(p=>!xiset.has(p.id)).sort((a,b)=>(a.pos==="GK"?-1:0)-(b.pos==="GK"?-1:0)).map(p=>p.id);
  if(S.cap&&!S.picks.includes(S.cap))S.cap=null; if(S.vice&&!S.picks.includes(S.vice))S.vice=null;
  if(!S.cap){ const best=xi.filter(p=>p.pos!=="GK").sort((a,b)=>MET(b)-MET(a))[0]; if(best)S.cap=best.id; }
}

// ---------- render top bar ----------
function renderBar(){
  const sp=spent(), rem=F.budget-sp, n=S.picks.length;
  const proj=n>=11?projOf(xiIds(),S.cap):0;
  const noCap = S.draft&&S.draft.active&&!S.draft.budgetOn;   // pure-skill draft: no salary cap
  $("#bar").innerHTML=
   (noCap?card(`£${sp.toFixed(0)}m`,"Squad value","no salary cap")
         :card(`£${rem.toFixed(1)}m`,"Budget left",`of £${F.budget.toFixed(1)}m`,`<div class="budbar"><i class="${rem<0?'over':''}" style="width:${Math.max(0,Math.min(100,100*sp/F.budget))}%"></i></div>`))
  +card(`${n}/15`,"Squad",n<15?`pick ${15-n} more`:"complete")
  +(F.started?card(`${totalPoints()}`,"Total points","captain doubled")
              :card(`${proj}`,"Projected pts","per matchday"))
  +(F.started?card(`MD${F.gws[F.gws.length-1]}`,"Latest matchday","scored so far")
             :card(`MD ${F.start_gw}`,"Season starts","points count from here"));
  const c=posCount(S.picks); const ok=n===15&&rem>=0&&c.GK===2&&c.DEF===5&&c.MID===5&&c.FWD===3&&!overTeam();
  $("#valid").innerHTML= n<15?`Pick ${15-n} more · need 2 GK, 5 DEF, 5 MID, 3 FWD`
    : rem<0?`<span style="color:var(--red)">£${(-rem).toFixed(1)}m over budget</span>`
    : overTeam()?`<span style="color:var(--red)">Max 3 players per country</span>`
    : !ok?`Need exactly 2 GK · 5 DEF · 5 MID · 3 FWD`:`<span style="color:var(--live)">✓ Valid squad — captain: ${F.byId[S.cap]?F.byId[S.cap].name:"—"}</span>`;
}
function card(v,l,s,extra){ return `<div class="bcard"><div class="bv">${v}</div><div class="bl">${l}</div>${s?`<div class="bs">${s}</div>`:""}${extra||""}</div>`; }
function overTeam(){ const c={}; let bad=false; picked().forEach(p=>{c[p.team]=(c[p.team]||0)+1; if(c[p.team]>F.max)bad=true;}); return bad; }

// ---------- player headshots (Wikipedia REST -> Wikidata -> number disc); cached in memory + localStorage,
//            footballer-verified, throttled with retry. Same cache key as the live page so photos are shared. ----------
function escAttr(s){ return String(s||"").replace(/&/g,"&amp;").replace(/"/g,"&quot;"); }
const PHOTOS={}, PHOTO_REQ={};
function photoGet(n){ if(n in PHOTOS) return PHOTOS[n]; try{const v=localStorage.getItem("wcph2:"+n); if(v) return (PHOTOS[n]=v);}catch(e){} return undefined; }
function photoSetPos(n,url){ PHOTOS[n]=url; try{localStorage.setItem("wcph2:"+n,url);}catch(e){} }
function photoSetNeg(n){ if(!(n in PHOTOS)) PHOTOS[n]=""; }
const FB_RE=/foot(ball)?|soccer|winger|midfield|defender|goalkeep|striker|forward/;
const psleep=ms=>new Promise(r=>setTimeout(r,ms));
let PHOTO_ACTIVE=0; const PHOTO_Q=[];
function photoSchedule(fn){ return new Promise(res=>{ PHOTO_Q.push({fn,res}); photoPump(); }); }
function photoPump(){ while(PHOTO_ACTIVE<3 && PHOTO_Q.length){ const job=PHOTO_Q.shift(); PHOTO_ACTIVE++;
  Promise.resolve().then(job.fn).then(v=>{PHOTO_ACTIVE--;job.res(v);photoPump();},()=>{PHOTO_ACTIVE--;job.res(null);photoPump();}); } }
async function pfetch(url){ for(let i=0;i<3;i++){ try{ const r=await fetch(url); if(r.status===429||r.status>=500){ await psleep(700*(i+1)+Math.random()*500); continue; } return r; }catch(e){ await psleep(500*(i+1)); } } return null; }
async function wikiSummaryPhoto(name){
  const r=await pfetch("https://en.wikipedia.org/api/rest_v1/page/summary/"+encodeURIComponent(name.replace(/ /g,"_"))+"?redirect=true");
  if(!r) return null; if(r.status===404) return ""; if(!r.ok) return null;
  try{ const d=await r.json(); if(!FB_RE.test(((d.description||"")+" "+(d.extract||"")).toLowerCase())) return ""; return (d.thumbnail||{}).source||""; }catch(e){ return null; }
}
async function wikidataPhoto(name){
  const r=await pfetch("https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&type=item&limit=5&origin=*&search="+encodeURIComponent(name));
  if(!r||!r.ok) return null; let qid=null;
  try{ const d=await r.json(); for(const h of (d.search||[])){ if(FB_RE.test((h.description||"").toLowerCase())){ qid=h.id; break; } } }catch(e){ return null; }
  if(!qid) return "";
  const r2=await pfetch("https://www.wikidata.org/w/api.php?action=wbgetclaims&format=json&property=P18&origin=*&entity="+encodeURIComponent(qid));
  if(!r2||!r2.ok) return null;
  try{ const d2=await r2.json(); const cl=(d2.claims&&d2.claims.P18)||[]; const fn=cl[0]&&cl[0].mainsnak&&cl[0].mainsnak.datavalue&&cl[0].mainsnak.datavalue.value;
    return fn ? "https://commons.wikimedia.org/wiki/Special:FilePath/"+encodeURIComponent(fn)+"?width=200" : ""; }catch(e){ return null; }
}
function fetchPlayerPhoto(name){
 const cached=photoGet(name); if(cached!==undefined) return Promise.resolve(cached);
 if(PHOTO_REQ[name]) return PHOTO_REQ[name];
 const p=(async()=>{
   const w=await photoSchedule(()=>wikiSummaryPhoto(name)); if(w){ photoSetPos(name,w); return w; }
   const d=await photoSchedule(()=>wikidataPhoto(name)); if(d){ photoSetPos(name,d); return d; }
   if(w!==null && d!==null) photoSetNeg(name);
   return "";
 })();
 PHOTO_REQ[name]=p;
 p.then(()=>{ if(photoGet(name)===undefined) delete PHOTO_REQ[name]; });
 return p;
}
function applyPhoto(el,url){ if(!url||!el)return; const img=new Image();
 img.onload=()=>{ el.style.backgroundImage="url('"+url.replace(/'/g,"%27")+"')"; el.classList.add("has-img"); }; img.src=url; }
function hydratePhotos(root){ (root||document).querySelectorAll(".phead[data-pl]").forEach(el=>{
 const nm=el.getAttribute("data-pl"); if(!nm)return;
 fetchPlayerPhoto(nm).then(url=>{ if(url) applyPhoto(el,url); }); }); }

// ---------- render pitch ----------
function jersey(p,fx,isBench){
  if(!p) return `<div class="slot" data-empty="1"><div class="jersey empty">+</div><div class="snm">&nbsp;</div></div>`;
  const capBadge=(!isBench&&S.cap===p.id)?`<span class="cap">C</span>`:(!isBench&&S.vice===p.id)?`<span class="cap v">V</span>`:"";
  const sub = fx? `${flag(p.team)} £${p.price.toFixed(1)}` : (F.started? `${p.pts}` : `x${(p.xpts||0).toFixed(1)}`);
  const last=p.name.split(" ").slice(-1)[0];
  return `<div class="slot" data-id="${p.id}"><div class="jersey phead" data-pl="${escAttr(p.name)}"><span class="pnum">${p.num||p.pos[0]}</span>${capBadge}</div><div class="snm">${flag(p.team)} ${last}</div><span class="spt${fx?' fx':''}">${sub}</span></div>`;
}
function renderPitch(){
  normaliseXI();
  const xi=xiIds().map(id=>F.byId[id]).filter(Boolean);
  const byPos={GK:[],DEF:[],MID:[],FWD:[]}; xi.forEach(p=>byPos[p.pos].push(p));
  // empty slots if incomplete
  const need={GK:2,DEF:5,MID:5,FWD:3};
  const pc=posCount(S.picks);
  const pitch=$("#pitch");
  const showVal = S.picks.length<15;   // show price while building, points once complete
  const rowFor=(arr,posKey,want)=>{
    let cells=arr.map(p=>jersey(p,showVal,false)).join("");
    // pad with empty pick slots for this position if still building XI shape
    return `<div class="line" data-pos="${posKey}">${cells||`<div class="slot" data-empty="1" data-pos="${posKey}"><div class="jersey empty">+</div><div class="snm">${posKey}</div></div>`}</div>`;
  };
  pitch.innerHTML = rowFor(byPos.GK,"GK")+rowFor(byPos.DEF,"DEF")+rowFor(byPos.MID,"MID")+rowFor(byPos.FWD,"FWD");
  // bench
  const bench=benchIds().map(id=>F.byId[id]).filter(Boolean);
  const benchCells = (bench.length?bench:[]).map(p=>jersey(p,showVal,true)).join("") || `<div class="slot" data-empty="1"><div class="jersey empty">+</div><div class="snm">bench</div></div>`;
  $("#bench").innerHTML=benchCells;
  hydratePhotos(pitch); hydratePhotos($("#bench"));   // fill in real headshots after the formation renders
  renderBar();
}

// ---------- scoring ----------
function gwScoreFor(ids,capId,viceId,gw){
  // ids = 11 starters; auto-sub non-players from bench (already excluded). returns points.
  const playing=id=>{const p=F.byId[id]; return p&&p.gw&&p.gw[gw]!=null;};
  let lineup=ids.slice();
  // auto-subs: replace non-playing starters with bench players that played, keeping formation legal
  const bench=benchIds().filter(id=>!ids.includes(id));
  const benchPlay=bench.filter(playing);
  const cnt=posCount(lineup);
  lineup=lineup.map(id=>{
    if(playing(id))return id;
    const p=F.byId[id];
    // find a bench replacement that keeps min counts and is available
    for(const bid of benchPlay){ const bp=F.byId[bid]; if(lineup.includes(bid))continue;
      if(p.pos==="GK"&&bp.pos!=="GK")continue;
      if(p.pos!=="GK"&&bp.pos==="GK")continue;
      return bid; }
    return id;
  });
  let pts=0;
  lineup.forEach(id=>{ const p=F.byId[id]; if(!p||!p.gw||p.gw[gw]==null)return;
    let v=p.gw[gw]; if(id===capId)v*=2; else if(id===viceId&&!playing(capId))v*=2; pts+=v; });
  return pts;
}
function totalPoints(){ if(S.picks.length<15)return 0; let t=0; F.gws.forEach(gw=>t+=gwScoreFor(xiIds(),S.cap,S.vice,String(gw))); return t; }

// dream team (best valid XI that gameweek, ignoring budget) — the ceiling
function dreamGW(gw){
  const played=F.players.filter(p=>p.gw&&p.gw[gw]!=null).map(p=>({...p,v:p.gw[gw]}));
  const byPos={GK:[],DEF:[],MID:[],FWD:[]}; played.forEach(p=>byPos[p.pos].push(p));
  for(const k in byPos)byPos[k].sort((a,b)=>b.v-a.v);
  if(!byPos.GK.length)return 0;
  const xi=[byPos.GK[0]]; const cnt={GK:1,DEF:0,MID:0,FWD:0};
  ["DEF","MID","FWD"].forEach(k=>{for(let i=0;i<FORM_MIN[k];i++)if(byPos[k][i]){xi.push(byPos[k][i]);cnt[k]++;}});
  const pool=[].concat(byPos.DEF.slice(FORM_MIN.DEF),byPos.MID.slice(FORM_MIN.MID),byPos.FWD.slice(FORM_MIN.FWD)).sort((a,b)=>b.v-a.v);
  let need=11-xi.length; for(const p of pool){if(need<=0)break; if(cnt[p.pos]<FORM_MAX[p.pos]){xi.push(p);cnt[p.pos]++;need--;}}
  let s=xi.reduce((a,p)=>a+p.v,0); const cap=xi.filter(p=>p.pos!=="GK").sort((a,b)=>b.v-a.v)[0]; if(cap)s+=cap.v; return s;
}
// ---------- AI rival managers (a deterministic league to compete against) ----------
function srng(s){ return function(){ s|=0; s=s+0x6D2B79F5|0; let t=Math.imul(s^s>>>15,1|s); t=t+Math.imul(t^t>>>7,61|t)^t; return ((t^t>>>14)>>>0)/4294967296; }; }
const MET=p=>(p.pts||0)*1000+(p.xpts||0);   // rank by actual points, then projection (so pre-season uses xPts)
function bestXIof(ids){
  const ps=ids.map(id=>F.byId[id]).filter(Boolean); const byPos={GK:[],DEF:[],MID:[],FWD:[]}; ps.forEach(p=>byPos[p.pos].push(p));
  for(const k in byPos)byPos[k].sort((a,b)=>MET(b)-MET(a)||b.price-a.price); if(!byPos.GK.length)return {xi:[],bench:[]};
  const xi=[byPos.GK[0]],cnt={GK:1,DEF:0,MID:0,FWD:0};
  ["DEF","MID","FWD"].forEach(k=>{for(let i=0;i<FORM_MIN[k];i++)if(byPos[k][i]){xi.push(byPos[k][i]);cnt[k]++;}});
  const pool=[].concat(byPos.DEF.slice(FORM_MIN.DEF),byPos.MID.slice(FORM_MIN.MID),byPos.FWD.slice(FORM_MIN.FWD)).sort((a,b)=>MET(b)-MET(a));
  let need=11-xi.length; for(const p of pool){if(need<=0)break;if(cnt[p.pos]<FORM_MAX[p.pos]){xi.push(p);cnt[p.pos]++;need--;}}
  const xs=new Set(xi.map(p=>p.id)); return {xi, bench:ps.filter(p=>!xs.has(p.id))};
}
function projOf(ids, capId){ const {xi}=bestXIof(ids); let s=xi.reduce((a,p)=>a+(p.xpts||0),0);
  const cp=F.byId[capId]; if(cp&&xi.some(p=>p.id===capId))s+=cp.xpts; else{const c=xi.filter(p=>p.pos!=="GK").sort((a,b)=>(b.xpts||0)-(a.xpts||0))[0]; if(c)s+=c.xpts;}
  return Math.round(s*10)/10; }
function scoreTeam(ids){
  const {xi,bench}=bestXIof(ids); if(xi.length<11)return {total:0,gw:{},cap:null,xi:[],value:0,proj:0};
  const cap=xi.filter(p=>p.pos!=="GK").sort((a,b)=>MET(b)-MET(a))[0]||xi[0]; const bids=bench.map(p=>p.id);
  const gw={}; let total=0;
  F.gws.forEach(g=>{ const G=String(g); const playing=id=>{const q=F.byId[id];return q&&q.gw&&q.gw[G]!=null;};
    const bp=bids.filter(playing); let line=xi.map(p=>p.id).map(id=>{ if(playing(id))return id; const p=F.byId[id];
      for(const b of bp){ if(line0has(line,b))continue; const q=F.byId[b]; if((p.pos==="GK")!==(q.pos==="GK"))continue; return b; } return id; });
    let s=0; line.forEach(id=>{const p=F.byId[id]; if(!p||!p.gw||p.gw[G]==null)return; let v=p.gw[G]; if(id===cap.id)v*=2; s+=v;}); gw[G]=s; total+=s; });
  return {total, gw, cap:cap.id, xi:xi.map(p=>p.id), value:ids.reduce((a,id)=>a+(F.byId[id]?F.byId[id].price:0),0), proj:projOf(ids, cap.id)};
}
function line0has(arr,x){ return arr.indexOf(x)>=0; }
// best-XI score for an arbitrary per-player metric m (captain doubled) — drives the optimizer
function bestXIByM(ids,m){
  const ps=ids.map(id=>F.byId[id]).filter(Boolean); const byPos={GK:[],DEF:[],MID:[],FWD:[]}; ps.forEach(p=>byPos[p.pos].push(p));
  for(const k in byPos)byPos[k].sort((a,b)=>m(b)-m(a)); if(!byPos.GK.length)return -1e9;
  const xi=[byPos.GK[0]],cnt={GK:1,DEF:0,MID:0,FWD:0};
  ["DEF","MID","FWD"].forEach(k=>{for(let i=0;i<FORM_MIN[k];i++)if(byPos[k][i]){xi.push(byPos[k][i]);cnt[k]++;}});
  const pool=[].concat(byPos.DEF.slice(FORM_MIN.DEF),byPos.MID.slice(FORM_MIN.MID),byPos.FWD.slice(FORM_MIN.FWD)).sort((a,b)=>m(b)-m(a));
  let need=11-xi.length; for(const p of pool){if(need<=0)break;if(cnt[p.pos]<FORM_MAX[p.pos]){xi.push(p);cnt[p.pos]++;need--;}}
  let s=xi.reduce((a,p)=>a+m(p),0); const cap=xi.filter(p=>p.pos!=="GK").sort((a,b)=>m(b)-m(a))[0]; if(cap)s+=m(cap);
  return s;
}
// strongest legal squad under the budget for metric m: cheapest valid start, then hill-climb
// same-position swaps that raise the best-XI score while staying within £budget (so it SPENDS
// the budget on the highest-projected players = the stars, instead of value-minning).
function optimizeSquad(m,budget){
  const need={GK:2,DEF:5,MID:5,FWD:3}, pool={}; POS.forEach(k=>pool[k]=F.players.filter(p=>p.pos===k).sort((a,b)=>m(b)-m(a)).slice(0,24));
  let picks=[]; const tc={};
  POS.forEach(k=>{ const cheap=F.players.filter(p=>p.pos===k).slice().sort((a,b)=>a.price-b.price); let got=0;
    for(const p of cheap){ if(got>=need[k])break; if((tc[p.team]||0)>=F.max)continue; picks.push(p.id);tc[p.team]=(tc[p.team]||0)+1;got++; } });
  const sp=()=>picks.reduce((s,id)=>s+(F.byId[id]?F.byId[id].price:0),0);
  // objective: best XI (captain doubled) + depth — the depth term spends spare budget on real
  // quality across all 15 instead of leaving a bench of £4.0 unknowns, so squads look world-class.
  const obj=ids=>{ let s=bestXIByM(ids,m); for(const id of ids){const p=F.byId[id]; if(p)s+=0.4*m(p);} return s; };
  for(let it=0;it<80;it++){
    const cur=obj(picks), spent=sp(); const c={}; picks.forEach(id=>{const t=F.byId[id].team;c[t]=(c[t]||0)+1;});
    let best=null,gain=1e-6;
    for(const oid of picks){ const o=F.byId[oid];
      for(const q of pool[o.pos]){ if(picks.includes(q.id))continue; if(spent-o.price+q.price>budget)continue;
        if(q.team!==o.team && (c[q.team]||0)>=F.max)continue;
        const np=picks.map(id=>id===oid?q.id:id); const g=obj(np)-cur; if(g>gain){gain=g;best=np;} } }
    if(!best)break; picks=best;
  }
  return picks;
}
let _MGRS=null,_MGRSseed=null;
function leagueSeed(){ return (S&&S.seed)||20260616; }
// Deterministic rival identities (names + drafting/strategy metrics) from a seed — shared by the
// salary-cap league build AND the draft, so a rival behaves the same whichever mode you're in.
function draftSetup(seed){
  const adj=["Galloping","Clinical","Rampant","Stubborn","Lethal","Rapid","Cunning","Mighty","Restless","Golden","Iron","Phantom","Rowdy","Daring","Sneaky","Electric","Rugged","Crafty","Bold","Savage","Royal","Frosty","Turbo","Velvet","Wily","Brave"];
  const noun=["Galácticos","Mavericks","Wizards","Underdogs","Tacticians","Renegades","Dynamos","Strikers","Hotshots","Rovers","Wanderers","Invincibles","Maestros","Outlaws","Titans","Comets","Pumas","Sharks","Falcons","Brigade","Legion","Mob","United","Athletic"];
  const r=srng(seed);
  const strongNats=[...new Set(F.players.filter(p=>p.xpts>=4.6).map(p=>p.team))];
  const pickNat=()=>strongNats.length?strongNats[Math.floor(r()*strongNats.length)]:null;
  const nat1=pickNat(); let nat2=pickNat(),g=0; while(nat2===nat1&&g++<8)nat2=pickNat();
  const styles=[
    p=>p.xpts+0.32*p.price,                                  // Galácticos — load the priciest stars
    p=>p.xpts-((p.xpts||0)>=4.6?2.1:0),                      // Differential — fade the obvious picks
    p=>p.xpts+(p.team===nat1?2.3:0),                         // National core #1
    p=>p.xpts+(p.team===nat2?2.3:0),                         // National core #2
    p=>p.xpts-0.11*Math.abs(p.price-7)                       // Mid-price moneyball (no premiums)
  ];
  const metrics=[]; for(let i=0;i<5;i++){ const sc0=styles[i]; const js=0.3+i*0.18;
    const jit={}; F.players.forEach(p=>jit[p.id]=(r()-0.5)*js); metrics.push(p=>sc0(p)+(jit[p.id]||0)); }
  const names=[]; const used=new Set(); for(let i=0;i<5;i++){ let nm,t=0; do{ nm=adj[Math.floor(r()*adj.length)]+" "+noun[Math.floor(r()*noun.length)]; }while(used.has(nm)&&t++<30); used.add(nm); names.push(nm); }
  return {metrics, names};
}
function genManagers(){
  // Draft mode: the rivals ARE the drafted rosters (exclusive players), scored live.
  if(S.draft&&S.draft.active){ const {names}=draftSetup(S.draft.seed);
    return names.map((nm,i)=>Object.assign({name:nm}, scoreTeam(S.draft.rosters[i]||[]))); }
  // Salary-cap mode: each rival optimizes its own archetype squad (players may overlap with yours).
  const seed=leagueSeed(); if(_MGRS&&_MGRSseed===seed)return _MGRS;
  const {metrics,names}=draftSetup(seed);
  const out=metrics.map((m,i)=>Object.assign({name:names[i]}, scoreTeam(optimizeSquad(m,F.budget))));
  _MGRS=out; _MGRSseed=seed; return out;
}

// ---------- DRAFT ENGINE: 6 managers (you + 5 rivals) draft an EXCLUSIVE pool in snake order ----------
const QUOTA={GK:2,DEF:5,MID:5,FWD:3};
function draftInit(seed,budgetOn){
  const r=srng(seed^0x5f3759df); const order=["me",0,1,2,3,4];
  for(let i=order.length-1;i>0;i--){ const j=Math.floor(r()*(i+1)); const t=order[i];order[i]=order[j];order[j]=t; }
  const rosters={},bud={}; order.forEach(s=>{rosters[s]=[];bud[s]=F.budget;});
  return {active:true, live:false, done:false, seed, budgetOn:!!budgetOn, order, pick:0, taken:{}, rosters, bud, log:[]};
}
function draftOnClock(D){ const round=Math.floor(D.pick/6), idx=D.pick%6; const seq=round%2===0?D.order:D.order.slice().reverse(); return seq[idx]; }
function draftPosCount(D,slot){ const c={GK:0,DEF:0,MID:0,FWD:0}; D.rosters[slot].forEach(id=>{const p=F.byId[id];if(p)c[p.pos]++;}); return c; }
// exact budget feasibility: after taking p, can this slot still fill its remaining quota from the
// currently-available pool within its remaining budget? (reserves the ACTUAL cheapest players left,
// not a flat £4 — so the draft never dead-ends.)
function draftReserveOK(D,slot,p){
  if(!D.budgetOn) return true;
  const c=draftPosCount(D,slot); const need={GK:QUOTA.GK-c.GK,DEF:QUOTA.DEF-c.DEF,MID:QUOTA.MID-c.MID,FWD:QUOTA.FWD-c.FWD}; need[p.pos]-=1;
  let cost=0;
  for(const pos of POS){ if(need[pos]<=0)continue;
    const a=F.players.filter(q=>q.pos===pos&&q.id!==p.id&&D.taken[q.id]==null).sort((x,y)=>x.price-y.price);
    if(a.length<need[pos]) return false;
    for(let i=0;i<need[pos];i++) cost+=a[i].price; }
  const slotsAfter=15-D.rosters[slot].length-1;            // headroom so 5 rivals draining cheap players between turns can't strand us
  return D.bud[slot]-p.price >= cost + 0.7*slotsAfter - 1e-9;
}
// never-fail fallback: cheapest available player for a still-needed position (ignores budget, so the
// draft physically cannot dead-lock; only rarely nudges an AI a pound or two over the cap).
function draftCheapestNeeded(D,slot){
  const c=draftPosCount(D,slot); const tc={}; D.rosters[slot].forEach(id=>{const q=F.byId[id];if(q)tc[q.team]=(tc[q.team]||0)+1;});
  let best=null;
  for(const p of F.players){ if(D.taken[p.id]!=null)continue; if(c[p.pos]>=QUOTA[p.pos])continue; if((tc[p.team]||0)>=F.max)continue; if(!best||p.price<best.price)best=p; }
  return best?best.id:null;
}
function draftCanTake(D,slot,p){
  if(D.taken[p.id]!=null) return false;
  if(draftPosCount(D,slot)[p.pos]>=QUOTA[p.pos]) return false;
  const tc={}; D.rosters[slot].forEach(id=>{const q=F.byId[id];if(q)tc[q.team]=(tc[q.team]||0)+1;}); if((tc[p.team]||0)>=F.max) return false;
  return draftReserveOK(D,slot,p);
}
function draftApply(D,slot,id){ const p=F.byId[id]; if(!p)return; D.taken[id]=slot; D.rosters[slot].push(id); if(D.budgetOn)D.bud[slot]-=p.price; D.log.push({slot,id}); D.pick++; }
// pick the best available draftable for a slot under metric — precomputes per-position availability
// + prefix sums so the exact budget-feasibility test is cheap across all candidates.
function draftBest(D,slot,metric){
  const c=draftPosCount(D,slot); const need={GK:QUOTA.GK-c.GK,DEF:QUOTA.DEF-c.DEF,MID:QUOTA.MID-c.MID,FWD:QUOTA.FWD-c.FWD};
  const tc={}; D.rosters[slot].forEach(id=>{const q=F.byId[id];if(q)tc[q.team]=(tc[q.team]||0)+1;});
  const PS={},RK={};
  if(D.budgetOn) for(const pos of POS){ const a=F.players.filter(q=>q.pos===pos&&D.taken[q.id]==null).sort((x,y)=>x.price-y.price);
    const ps=[0],rk={}; for(let i=0;i<a.length;i++){ps.push(ps[i]+a[i].price);rk[a[i].id]=i;} PS[pos]=ps;RK[pos]=rk; }
  const slotsAfter=15-D.rosters[slot].length-1;
  const feas=p=>{ if(!D.budgetOn)return true; let cost=0;
    for(const pos of POS){ let n=need[pos]; if(pos===p.pos)n-=1; if(n<=0)continue; const ps=PS[pos];
      if(pos===p.pos){ const idx=RK[pos][p.id]; if(idx<n){ if(ps.length<n+2)return false; cost+=ps[n+1]-p.price; } else { if(ps.length<n+1)return false; cost+=ps[n]; } }
      else { if(ps.length<n+1)return false; cost+=ps[n]; } }
    return D.bud[slot]-p.price>=cost + 0.7*slotsAfter - 1e-9; };
  let best=null,bv=-1e9;
  for(const p of F.players){ if(D.taken[p.id]!=null)continue; if(need[p.pos]<=0)continue; if((tc[p.team]||0)>=F.max)continue; if(!feas(p))continue; const v=metric(p); if(v>bv){bv=v;best=p;} }
  return best?best.id:null; }
// metric for a given slot: rivals use their archetype, you maximize projection
function draftMetricFor(D,slot){ if(slot==="me")return p=>p.xpts||0; const {metrics}=draftSetup(D.seed); return metrics[slot]; }
// run AI picks until it's your turn (or the draft ends); returns the slot now on the clock (or null if done)
function draftRunToUser(D){ const setup=draftSetup(D.seed);
  while(D.pick<90){ const slot=draftOnClock(D); if(slot==="me")return "me";
    const id=draftBest(D,slot,setup.metrics[slot])||draftCheapestNeeded(D,slot); if(id==null){D.pick++;continue;} draftApply(D,slot,id); }
  D.done=true; return null; }
// instant full draft: every slot auto-picks (rivals by archetype, you by projection) to completion
function draftRunAll(D){ const setup=draftSetup(D.seed);
  while(D.pick<90){ const slot=draftOnClock(D); const m=slot==="me"?(p=>p.xpts||0):setup.metrics[slot];
    const id=draftBest(D,slot,m)||draftCheapestNeeded(D,slot); if(id==null){D.pick++;continue;} draftApply(D,slot,id); }
  D.done=true; return D; }

// ---------- DRAFT UI / controller ----------
function draftBudgetOn(){ return S.budgetMode!==false; }   // toggle, default on
function freshSeed(){ return (Date.now()^Math.floor(Math.random()*1e9))>>>0; }
function draftNameFn(){ const {names}=draftSetup(S.draft.seed); return s=>s==="me"?"You":names[s]; }
function syncSquadFromDraft(){ const D=S.draft; S.picks=(D.rosters["me"]||[]).slice();
  if(S.cap&&!S.picks.includes(S.cap))S.cap=null; if(S.vice&&!S.picks.includes(S.vice))S.vice=null;
  S.bench=[]; if(S.picks.length>=15)normaliseXI(); }
// instant auto-draft (you + 5 rivals at once)
function autoDraftMine(){
  S.cap=null; S.vice=null; S.draft=draftInit(freshSeed(),draftBudgetOn()); draftRunAll(S.draft); S.draft.live=false;
  S.seed=S.draft.seed; syncSquadFromDraft(); save(); renderPitch(); renderPoints();
  toast("Drafted your 15 — every player is now exclusive");
}
// free a player back to the pool (post-draft edit)
function draftFree(id){ const D=S.draft,p=F.byId[id]; if(!D||D.taken[id]!=="me"||!p)return; D.rosters["me"]=D.rosters["me"].filter(x=>x!==id); delete D.taken[id]; if(D.budgetOn)D.bud["me"]=Math.min(F.budget,D.bud["me"]+p.price); }
// post-draft: sign an undrafted free agent (auto-drops weakest same-pos if that slot is full)
function draftUserAdd(id){ const D=S.draft,p=F.byId[id]; if(!p)return;
  if(D.taken[id]!=null){ toast(D.taken[id]==="me"?"Already in your squad":"A rival owns him"); return; }
  const tc={}; D.rosters["me"].forEach(x=>{const q=F.byId[x];if(q)tc[q.team]=(tc[q.team]||0)+1;});
  if((tc[p.team]||0)>=F.max){ toast("Max 3 from "+p.team); return; }
  if(draftPosCount(D,"me")[p.pos]>=QUOTA[p.pos]){ const same=D.rosters["me"].map(x=>F.byId[x]).filter(x=>x&&x.pos===p.pos).sort((a,b)=>(a.xpts||0)-(b.xpts||0)); if(same[0])draftFree(same[0].id); }
  if(D.budgetOn && D.bud["me"]-p.price < -1e-9){ toast("Not enough budget (£"+D.bud["me"].toFixed(1)+" left)"); return; }
  D.taken[id]="me"; D.rosters["me"].push(id); if(D.budgetOn)D.bud["me"]-=p.price;
  syncSquadFromDraft(); save(); closePicker(); renderPitch(); renderPoints(); toast(p.name+" signed");
}
function draftUserRemove(id){ if(S.cap===id)S.cap=null; if(S.vice===id)S.vice=null; draftFree(id); syncSquadFromDraft(); save(); renderPitch(); renderPoints(); }

// ----- live snake draft -----
const DRAFT_DELAY=170;
function startLiveDraft(){
  S.cap=null; S.vice=null; S.draft=draftInit(freshSeed(),draftBudgetOn()); S.draft.live=true; S.seed=S.draft.seed;
  syncSquadFromDraft(); $("#draftlog").innerHTML=""; $("#draftov").classList.add("show"); renderDraftBoard(); save();
  setTimeout(draftStep,400);
}
function draftStep(){
  const D=S.draft; if(!D||!D.live)return;
  if(D.pick>=90){ finishLiveDraft(); return; }
  const slot=draftOnClock(D); renderDraftBoard();
  if(slot==="me"){ $("#draftstatus").innerHTML=`<span style="color:var(--live)">🟢 You're on the clock</span> <button class="btn solid gobtn" id="dpick">Pick a player</button>`; const b=$("#dpick"); if(b)b.onclick=openDraftPicker; openDraftPicker(); return; }
  const setup=draftSetup(D.seed);
  const id=draftBest(D,slot,setup.metrics[slot])||draftCheapestNeeded(D,slot);
  if(id==null){ D.pick++; setTimeout(draftStep,10); return; }
  draftApply(D,slot,id); appendDraftLog(slot,id); renderDraftBoard();
  setTimeout(draftStep,DRAFT_DELAY);
}
function userDraftTake(id){ const D=S.draft; if(!D||!D.live||draftOnClock(D)!=="me")return;
  const p=F.byId[id]; if(!p||D.taken[id]!=null){ toast("Unavailable"); return; }
  if(!draftCanTake(D,"me",p)){ toast(D.budgetOn?"Can't afford him & still fill 15":"Position full or 3-per-nation"); return; }
  draftApply(D,"me",id); appendDraftLog("me",id); closePicker(); syncSquadFromDraft(); save(); renderDraftBoard();
  $("#draftstatus").innerHTML=`<b>${flag(p.team)} ${p.name}</b> — nice pick! Rivals drafting…`;
  setTimeout(draftStep,150);
}
function finishLiveDraft(){ const D=S.draft; if(!D)return; D.live=false; D.done=true; syncSquadFromDraft(); save();
  renderDraftBoard(); renderPitch(); renderPoints();
  $("#draftttl").textContent="🎯 Draft complete"; $("#draftstatus").innerHTML=`<b>✅ Your 15 are locked in.</b> Close this, then tap a starter on the pitch to set your captain. <button class="btn solid gobtn" id="draftdone">View my team</button>`;
  const b=$("#draftdone"); if(b)b.onclick=()=>$("#draftov").classList.remove("show");
}
function renderDraftBoard(){ const D=S.draft; if(!D)return; const nm=draftNameFn();
  const oc=D.pick<90?draftOnClock(D):null; const round=Math.min(15,Math.floor(D.pick/6)+1);
  $("#draftttl").textContent=`🎯 Live Draft · Round ${round}/15`;
  $("#draftboard").innerHTML=D.order.map(s=>`<div class="dchip ${s===oc?'onclock':''} ${s==='me'?'mechip':''}"><div class="dc">${D.rosters[s].length}<span style="font-size:10px;color:var(--mut)">/15</span></div><div class="dn">${s==='me'?'⭐ You':nm(s)}</div></div>`).join("");
}
function appendDraftLog(slot,id){ const D=S.draft; const nm=draftNameFn(); const p=F.byId[id]; if(!p)return; const round=Math.floor((D.pick-1)/6)+1;
  const row=document.createElement("div"); row.className="dlogrow"+(slot==="me"?" mine":"");
  row.innerHTML=`<span class="rr">R${round}·#${D.pick}</span><span class="pp phead" data-pl="${escAttr(p.name)}"></span><span><b>${slot==="me"?"⭐ You":nm(slot)}</b> → ${flag(p.team)} ${p.name} <span style="color:var(--mut)">£${p.price.toFixed(1)} · ${p.pos}</span></span>`;
  const log=$("#draftlog"); if(log){ log.insertBefore(row,log.firstChild); hydratePhotos(row); }
}
function openDraftPicker(){ pickFor={draft:true}; $("#pickttl").textContent="Draft a player — you're on the clock"; $("#fsearch").value=""; renderPickList(); $("#pickov").classList.add("show"); }
function showManager(m){
  const xi=(m.xi||[]).map(id=>F.byId[id]).filter(Boolean);
  const byPos={GK:[],DEF:[],MID:[],FWD:[]}; xi.forEach(p=>byPos[p.pos].push(p));
  const chip=p=>`<span class="mchip"><span class="phead mhead" data-pl="${escAttr(p.name)}"></span>${flag(p.team)} ${p.name.split(" ").slice(-1)[0]}${p.id===m.cap?' <b>(C)</b>':''}</span>`;
  const line=k=>byPos[k].map(chip).join("")||"—";
  const head=F.started?`<b>${m.total}</b> pts`:`<b>${m.proj}</b> projected pts/MD`;
  $("#mgrname").textContent=m.name; $("#mgrbody").innerHTML=
    `<div class="hint" style="padding:8px 16px">${head} · squad £${m.value.toFixed(1)}m</div>`+
    POS.map(k=>`<div class="gwrow"><div style="width:100%"><div class="gwn" style="font-size:12px;color:var(--mut)">${k}</div><div style="display:flex;flex-wrap:wrap">${line(k)}</div></div></div>`).join("");
  hydratePhotos($("#mgrov")); $("#mgrov").classList.add("show");
}
function renderPoints(){
  const box=$("#ptsbox"); const started=F.started;
  if(S.picks.length<15){ box.innerHTML=`<div class="empty">Pick a full 15-player squad to enter the league.</div>`; return; }
  const mine=totalPoints(); const myProj=projOf(xiIds(),S.cap);
  const mgrs=genManagers();
  const myGw=Object.fromEntries(F.gws.map(g=>[String(g),gwScoreFor(xiIds(),S.cap,S.vice,String(g))]));
  const me={name:"⭐ Your team",total:mine,proj:myProj,value:spent(),cap:S.cap,xi:xiIds(),gw:myGw,me:true};
  const rv=t=>(started?t.total:t.proj)*1000 - t.value;   // rank by score, tiebreak cheaper squad
  const table=[me].concat(mgrs).sort((a,b)=>rv(b)-rv(a));
  const myRank=table.findIndex(t=>t.me)+1;
  const lastGW=F.gws.length?String(F.gws[F.gws.length-1]):null;
  const rows=table.map((t,i)=>{ const gwp=lastGW&&t.gw?(t.gw[lastGW]||0):0; const mi=t.me?-1:mgrs.indexOf(t);
    return `<tr class="${t.me?'meRow':''}" data-mgr="${mi}"><td class="n">${i+1}</td><td>${t.name}</td><td class="n">£${t.value.toFixed(1)}</td>${started?`<td class="n">${gwp}</td>`:''}<td class="n"><b>${started?t.total:t.proj}</b></td></tr>`; }).join("");
  const tier=myRank===1?"🏆 Top of the league!":myRank<=Math.ceil(table.length*0.25)?"Top-quarter — strong squad 🔥":myRank<=Math.ceil(table.length*0.5)?"Upper half — keep tinkering":"Room to climb — chase value &amp; a big captain";
  const startCard = started?"":`<div class="card" style="border:1px solid var(--blue)"><div class="hint" style="color:var(--txt);padding:13px 16px;font-size:13.5px"><b>🚦 Your season kicks off at Matchday ${F.start_gw}.</b> The tournament was already under way, so — to keep it fair — your team only scores from Matchday ${F.start_gw} onward. Matchday 1 counts as <b>form</b> only (it sets prices, it doesn't score). Build the best squad you can now; the table below ranks everyone by <b>projected</b> points until kick-off.</div></div>`;
  box.innerHTML= startCard+
   `<div class="card"><h3>Your season</h3>`+
   (started
     ?`<div class="cmp"><span><b>Total points</b></span><span class="cv" style="font-size:22px">${mine}</span></div>`
     :`<div class="cmp"><span><b>Projected points</b> <span style="color:var(--mut);font-weight:600;font-size:11px">per matchday</span></span><span class="cv" style="font-size:22px">${myProj}</span></div>`)+
   `<div class="cmp"><span>League position</span><span class="cv">${myRank}<span style="color:var(--mut);font-weight:600">/${table.length}</span></span></div>`+
   `<div class="hint">${tier}</div></div>`+
   `<div class="card"><h3>${started?"League table":"Projected league"} <span style="font-weight:600;color:var(--mut);font-size:11px">you vs ${mgrs.length} rivals</span></h3><div class="tscroll"><table class="tbl" id="ltbl"><thead><tr><th class="n">#</th><th>Manager</th><th class="n">Squad £</th>${started?`<th class="n">MD ${lastGW||"—"}</th>`:''}<th class="n">${started?"Total":"Proj"}</th></tr></thead><tbody>${rows}</tbody></table></div><div class="hint">Tap any rival to see their XI. Managers are AI-built with different strategies${started?" and scored on the same real results":", and pick from the same projections you do"}.</div></div>`+
   (started?`<div class="card"><h3>Gameweek by gameweek</h3>`+F.gws.map(gw=>{const m=gwScoreFor(xiIds(),S.cap,S.vice,String(gw)),dr=dreamGW(String(gw));return `<div class="gwrow"><div><div class="gwn">Matchday ${gw}</div><div class="gwsub">dream team ${dr}</div></div><div class="gwp">${m}</div></div>`;}).join("")+`</div>`:"");
}

// ---------- player picker ----------
function openPicker(pos){ pickFor={pos}; $("#pickttl").textContent="Pick a "+pos; $("#fsearch").value=""; renderPickList(); $("#pickov").classList.add("show"); }
function closePicker(){ $("#pickov").classList.remove("show"); pickFor=null; }
function draftTeamCount(slot,team){ return (S.draft.rosters[slot]||[]).filter(x=>F.byId[x]&&F.byId[x].team===team).length; }
function renderPickList(){
  const draftMode=pickFor&&pickFor.draft; const D=S.draft, dActive=D&&D.active;
  const q=$("#fsearch").value.toLowerCase(); const team=$("#fteam").value; const sort=$("#fsort").value;
  const rem = dActive ? (D.budgetOn?D.bud["me"]:99999) : (F.budget-spent());
  let list;
  if(draftMode){ const need=draftPosCount(D,"me"); list=F.players.filter(p=>D.taken[p.id]==null && need[p.pos]<QUOTA[p.pos]); }
  else { const pos=pickFor.pos; list=F.players.filter(p=>p.pos===pos); if(dActive)list=list.filter(p=>D.taken[p.id]==null); }
  if(team)list=list.filter(p=>p.team===team);
  if(q)list=list.filter(p=>p.name.toLowerCase().includes(q)||p.team.toLowerCase().includes(q));
  const projM=F.started?(p=>p.pts):(p=>p.xpts||0);
  list.sort(sort==="price"?(a,b)=>b.price-a.price : sort==="value"?(a,b)=>((b.xpts+0.5)/b.price)-((a.xpts+0.5)/a.price) : sort==="form"?(a,b)=>(b.form||0)-(a.form||0)||projM(b)-projM(a) : (a,b)=>projM(b)-projM(a)||b.price-a.price);
  $("#plist").innerHTML=list.slice(0,240).map(p=>{
    const own=dActive?(D.taken[p.id]==="me"):S.picks.includes(p.id);
    const tcFull=(dActive?draftTeamCount("me",p.team):teamCount(p.team))>=F.max&&!own;
    const afford=(dActive&&!D.budgetOn)?true:(p.price<=rem||own);
    const dis=own||tcFull||!afford; const fm=p.form||0;
    const metaR=F.started?`<div class="ppt">${p.pts} pts</div>`:`<div class="ppt" title="projected points per matchday">x${(p.xpts||0).toFixed(1)}${fm?` · <span style="color:var(--mut)">${fm} form</span>`:''}</div>`;
    return `<div class="pl ${dis?'dis':''}" data-pick="${p.id}"><div><span class="pos-tag pos-${p.pos}">${p.pos}</span><span class="pnm">${flag(p.team)} ${p.name}</span><div class="psub">${p.team}${tcFull?' · 3 already':''}${own?' · yours':''}${!afford?' · too expensive':''}</div></div><div class="ppr">£${p.price.toFixed(1)}</div>${metaR}</div>`;
  }).join("")||`<div class="empty">${draftMode?"No available players for your open positions.":"No available players match."}</div>`;
}
function pick(id){
  if(S.draft&&S.draft.active){ if(S.draft.live&&draftOnClock(S.draft)==="me")return userDraftTake(id); return draftUserAdd(id); }
  const p=F.byId[id]; if(!p)return;
  if(S.picks.includes(id)){toast("Already in your squad");return;}
  if(teamCount(p.team)>=F.max){toast("Max 3 from "+p.team);return;}
  const cap=F.squad[p.pos]; const cur=picked().filter(x=>x.pos===p.pos);
  if(cur.length>=cap){ const dk=F.started?(x=>x.pts):(x=>x.xpts||0);
    const drop=cur.sort((a,b)=>dk(a)-dk(b)||a.price-b.price)[0];
    S.picks=S.picks.filter(x=>x!==drop.id); if(S.cap===drop.id)S.cap=null; if(S.vice===drop.id)S.vice=null; }
  if(spent()+p.price>F.budget){ toast("Not enough budget"); }
  S.picks.push(id); S.bench=[]; normaliseXI(); save(); closePicker(); renderPitch(); renderPoints(); toast(p.name+" added");
}
function removePlayer(id){
  if(S.draft&&S.draft.active)return draftUserRemove(id);
  S.picks=S.picks.filter(x=>x!==id); if(S.cap===id)S.cap=null; if(S.vice===id)S.vice=null; S.bench=S.bench.filter(x=>x!==id); normaliseXI(); save(); renderPitch(); renderPoints(); }

// ---------- players table ----------
let sortKey="xpts",sortDir=-1;
function renderTable(){
  const q=$("#psearch").value.toLowerCase(); const pf=$("#pposf").value;
  let list=F.players.slice(); if(pf)list=list.filter(p=>p.pos===pf);
  if(q)list=list.filter(p=>p.name.toLowerCase().includes(q)||p.team.toLowerCase().includes(q));
  const vof=p=>((p.xpts||0)+0.5)/p.price;
  list.sort((a,b)=>{const k=sortKey; if(k==="name"||k==="team")return sortDir*(""+a[k]).localeCompare(""+b[k]); let av=k==="value"?vof(a):(a[k]||0), bv=k==="value"?vof(b):(b[k]||0); return sortDir*(bv-av);});
  const th=(k,l,t)=>`<th class="n" data-k="${k}"${t?` title="${t}"`:""}>${l}${sortKey===k?(sortDir<0?" ▾":" ▴"):""}</th>`;
  $("#ptbl").innerHTML=`<thead><tr><th data-k="name">Player${sortKey==="name"?(sortDir<0?" ▾":" ▴"):""}</th><th data-k="team">Team${sortKey==="team"?(sortDir<0?" ▾":" ▴"):""}</th><th data-k="pos">Pos</th>${th("price","Price")}${th("xpts","xPts","projected points / matchday")}${th("form","Form","points on matchday 1 (does not score)")}${F.started?th("pts","Pts","points scored this season"):""}${th("value","Value","projection per £")}</tr></thead><tbody>`+
   list.slice(0,300).map(p=>`<tr><td>${flag(p.team)} ${p.name} ${S.picks.includes(p.id)?'<span style="color:var(--live)">●</span>':''}</td><td>${p.team}</td><td><span class="pos-tag pos-${p.pos}">${p.pos}</span></td><td class="n">£${p.price.toFixed(1)}</td><td class="n"><b>${(p.xpts||0).toFixed(1)}</b></td><td class="n">${p.form||0}</td>${F.started?`<td class="n">${p.pts}</td>`:""}<td class="n">${vof(p).toFixed(1)}</td></tr>`).join("")+`</tbody>`;
}

// ---------- events ----------
function bind(){
  document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>{document.querySelectorAll(".tab").forEach(x=>x.classList.remove("on"));t.classList.add("on");
    document.querySelectorAll(".sec").forEach(s=>s.classList.remove("on")); $("#sec-"+t.dataset.sec).classList.add("on");
    if(t.dataset.sec==="players")renderTable(); if(t.dataset.sec==="points")renderPoints();});
  $("#pitch").addEventListener("click",e=>{ const slot=e.target.closest(".slot"); if(!slot)return;
    if(slot.dataset.empty){ const pos=slot.closest(".line").dataset.pos; openPicker(pos); return; }
    const id=slot.dataset.id; if(!id)return; // tap starter -> captain cycle
    if(S.cap===id){S.cap=S.vice;S.vice=id;} else if(S.vice===id){S.vice=null;} else if(!S.cap){S.cap=id;} else {S.vice=id;}
    save(); renderPitch();
  });
  $("#pitch").addEventListener("contextmenu",e=>{const slot=e.target.closest(".slot[data-id]");if(slot){e.preventDefault();if(confirm("Remove this player?"))removePlayer(slot.dataset.id);}});
  $("#bench").addEventListener("click",e=>{const slot=e.target.closest(".slot");if(!slot)return; if(slot.dataset.empty){openPicker("GK");return;} });
  $("#pickx").onclick=closePicker; $("#pickov").addEventListener("click",e=>{if(e.target===$("#pickov"))closePicker();});
  $("#plist").addEventListener("click",e=>{const r=e.target.closest(".pl[data-pick]"); if(r&&!r.classList.contains("dis"))pick(r.dataset.pick);});
  ["#fsearch","#fteam","#fsort"].forEach(s=>$(s).addEventListener("input",renderPickList));
  $("#livedraft").onclick=()=>{ if(S.picks.length&&!confirm("Start a new live draft? This replaces your current squad."))return; startLiveDraft(); };
  $("#autodraft").onclick=()=>{ if(S.picks.length&&!confirm("Auto-draft a new squad? This replaces your current one."))return; autoDraftMine(); };
  $("#budtoggle").onchange=e=>{ S.budgetMode=e.target.checked; save(); renderBar(); toast(e.target.checked?"Salary cap ON — £100 budget":"Salary cap OFF — pure skill draft"); };
  $("#draftx").onclick=()=>{ const D=S.draft; if(D&&D.live){ const setup=draftSetup(D.seed);  // leaving early auto-completes the rest
      while(D.pick<90){const slot=draftOnClock(D);const m=slot==="me"?(p=>p.xpts||0):setup.metrics[slot];const id=draftBest(D,slot,m)||draftCheapestNeeded(D,slot);if(id==null){D.pick++;continue;}draftApply(D,slot,id);} finishLiveDraft(); } $("#draftov").classList.remove("show"); };
  $("#reset").onclick=()=>{if(confirm("Clear your squad and draft?")){S={picks:[],cap:null,vice:null,bench:[],budgetMode:S.budgetMode};save();renderPitch();renderPoints();}};
  $("#share").onclick=()=>{ if(S.picks.length<15){toast("Build a full squad first");return;} const ids=xiIds().concat(benchIds()).concat([S.cap||"",S.vice||""]);
    const url=location.origin+location.pathname+"?t="+ids.join("."); navigator.clipboard&&navigator.clipboard.writeText(url); toast("Share link copied!"); };
  $("#ptbl").addEventListener("click",e=>{const th=e.target.closest("th[data-k]");if(!th)return;const k=th.dataset.k; if(sortKey===k)sortDir*=-1;else{sortKey=k;sortDir=(k==="name"||k==="team")?1:-1;}renderTable();});
  ["#psearch","#pposf"].forEach(s=>$(s).addEventListener("input",renderTable));
  $("#ptsbox").addEventListener("click",e=>{ const tr=e.target.closest("tr[data-mgr]"); if(!tr)return; const mi=+tr.dataset.mgr; if(mi>=0){ const m=genManagers()[mi]; if(m)showManager(m); } });
  $("#mgrx").onclick=()=>$("#mgrov").classList.remove("show"); $("#mgrov").addEventListener("click",e=>{if(e.target===$("#mgrov"))$("#mgrov").classList.remove("show");});
  if("serviceWorker" in navigator)addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));
}

fetch("fantasy.json",{cache:"no-store"}).then(r=>r.json()).then(d=>{
  F.budget=d.budget; F.squad=d.squad; F.max=d.max_per_team; F.players=d.players; F.start_gw=d.start_gw||1;
  F.players.forEach(p=>F.byId[p.id]=p);
  const gws=new Set(); F.players.forEach(p=>{for(const g in (p.gw||{}))if(+g>=F.start_gw)gws.add(+g);}); F.gws=[...gws].sort((a,b)=>a-b);
  F.started=F.gws.length>0;
  // team filter options
  const teams=[...new Set(F.players.map(p=>p.team))].sort();
  $("#fteam").innerHTML=`<option value="">All teams</option>`+teams.map(t=>`<option>${t}</option>`).join("");
  load(); bind(); const bt=$("#budtoggle"); if(bt)bt.checked=draftBudgetOn(); renderPitch(); renderPoints();
}).catch(e=>{ $("#bar").innerHTML=`<div class="bcard"><div class="bv">—</div><div class="bl">Fantasy data loading…</div><div class="bs">refresh in a moment</div></div>`; });
</script>
</body>
</html>"""

doc = HTML.replace("__FLAGS__", json.dumps(FLAGS, ensure_ascii=False))
open("website/fantasy.html", "w").write(doc)
# the page fetches ./fantasy.json — publish the latest player DB alongside it
if os.path.exists("data/fantasy.json"):
    import shutil; shutil.copy("data/fantasy.json", "website/fantasy.json")
print(f"website/fantasy.html written ({len(doc)//1024} KB); fantasy.json copied")
