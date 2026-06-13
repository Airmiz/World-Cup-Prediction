"""Assemble website/live.html — self-contained live page:
embedded engine data + Monte Carlo engine + live results fetch + UI."""
import json

DATA = open("website/live_data.json", encoding="utf-8").read()
ENGINE = open("src/live_engine.js", encoding="utf-8").read()
INPLAY = open("src/inplay.js", encoding="utf-8").read()

FEED_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Cup 26 — Live</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='t' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%2300854d'/%3E%3Cstop offset='.52' stop-color='%231e6fd9'/%3E%3Cstop offset='1' stop-color='%23d92d2d'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='64' height='64' rx='15' fill='url(%23t)'/%3E%3Ctext x='32' y='44' font-family='-apple-system,Helvetica,Arial' font-size='32' font-weight='800' font-style='italic' fill='white' text-anchor='middle'%3E26%3C/text%3E%3C/svg%3E">
<style>
:root{--bg:#f5f5f7;--surface:#fff;--txt:#1d1d1f;--mut:#6e6e73;--hair:#d2d2d7;
 --g1:#00854d;--g2:#1e6fd9;--g3:#d92d2d;--tri:linear-gradient(90deg,var(--g1),var(--g2) 52%,var(--g3));
 --blue:var(--g2);--blue-soft:rgba(30,111,217,.10);--green:#34c759;--red:#ff3b30;--amber:#ff9f0a;
 --track:#e8e8ed;--shadow:0 4px 24px rgba(0,0,0,.06),0 1px 3px rgba(0,0,0,.04);
 --shadow-lg:0 12px 48px rgba(0,0,0,.10);--radius:18px;--nav-bg:rgba(251,251,253,.82);--tint:#fbfbfd;--live:#ff3b30}
@media(prefers-color-scheme:dark){:root{--bg:#000;--surface:#1c1c1e;--txt:#f5f5f7;--mut:#86868b;--hair:#38383a;
 --g1:#2fbf7f;--g2:#3f8cff;--g3:#ff5d5d;--blue:var(--g2);--blue-soft:rgba(63,140,255,.18);--track:#2c2c2e;
 --shadow:0 4px 24px rgba(0,0,0,.5);--shadow-lg:0 12px 48px rgba(0,0,0,.6);--nav-bg:rgba(22,22,23,.8);--tint:#101012;--live:#ff453a}}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--txt);overflow-x:hidden;
 font:16px/1.6 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--blue);text-decoration:none}
nav{position:sticky;top:0;z-index:100;background:var(--nav-bg);backdrop-filter:saturate(1.8) blur(20px);-webkit-backdrop-filter:saturate(1.8) blur(20px);border-bottom:1px solid rgba(0,0,0,.08)}
@media(prefers-color-scheme:dark){nav{border-bottom-color:rgba(255,255,255,.1)}}
nav .in{max-width:1180px;margin:0 auto;display:flex;align-items:center;gap:8px;padding:0 22px;height:48px;overflow-x:auto;scrollbar-width:none}
nav .in::-webkit-scrollbar{display:none}
nav b{display:flex;align-items:center;font-size:14px;font-weight:600;margin-right:auto;white-space:nowrap}
.lg{display:inline-flex;align-items:center;justify-content:center;width:27px;height:27px;border-radius:8px;background:var(--tri);color:#fff;font-weight:800;font-size:13px;margin-right:9px;font-style:italic;box-shadow:0 2px 8px rgba(30,111,217,.35)}
nav a{color:var(--txt);opacity:.75;font-size:12.5px;padding:5px 12px;border-radius:999px;white-space:nowrap;font-weight:500;transition:.25s}
nav a:hover,nav a.on{opacity:1;background:var(--blue-soft);color:var(--blue);text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px 110px}
section{margin-top:60px;scroll-margin-top:64px}
.shead{max-width:820px;margin:0 auto 26px;text-align:center}
.shead h2{font-size:clamp(26px,3.6vw,38px);font-weight:700;letter-spacing:-.02em}
.shead h2::after{content:"";display:block;width:54px;height:4px;border-radius:3px;background:var(--tri);margin:13px auto 0}
.shead p{color:var(--mut);font-size:16px;margin-top:12px}
/* hero / status */
header.hero{padding:54px 16px 0;text-align:center}
.livetag{display:inline-flex;align-items:center;gap:8px;font-weight:700;letter-spacing:.08em;font-size:13px;color:var(--live)}
.pulse{width:10px;height:10px;border-radius:50%;background:var(--live);box-shadow:0 0 0 0 rgba(255,59,48,.6);animation:pulse 1.8s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(255,59,48,.55)}70%{box-shadow:0 0 0 12px rgba(255,59,48,0)}100%{box-shadow:0 0 0 0 rgba(255,59,48,0)}}
.hero h1{font-size:clamp(34px,6vw,62px);font-weight:700;letter-spacing:-.03em;line-height:1.05;margin-top:12px}
.hero h1 .grad{background:var(--tri);-webkit-background-clip:text;background-clip:text;color:transparent}
.statusbar{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;align-items:center;margin:22px auto 0;max-width:900px}
.pill{display:inline-flex;align-items:center;gap:8px;background:var(--surface);border-radius:999px;padding:8px 16px;box-shadow:var(--shadow);font-size:13px;color:var(--mut)}
.pill b{color:var(--txt);font-weight:600}
.pill .dot{width:7px;height:7px;border-radius:50%;flex:none}
.dot.ok{background:var(--green)}.dot.warn{background:var(--amber)}.dot.err{background:var(--red)}
button.btn{font-family:inherit;cursor:pointer;border:none;background:var(--blue);color:#fff;border-radius:999px;padding:8px 18px;font-size:13px;font-weight:600;transition:.2s}
button.btn:hover{filter:brightness(1.08)}
button.btn.ghost{background:var(--surface);color:var(--blue);box-shadow:var(--shadow)}
.bigstat{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px;max-width:920px;margin:30px auto 0}
.bs{position:relative;overflow:hidden;background:var(--surface);border-radius:var(--radius);padding:22px;box-shadow:var(--shadow);text-align:left}
.bs::before{content:"";position:absolute;inset:0 auto auto 0;height:4px;width:100%;background:var(--tri)}
.bs .v{font-size:26px;font-weight:700;letter-spacing:-.02em;margin-top:4px}
.bs .k{color:var(--mut);font-size:12.5px}
.bs .d{font-size:12px;font-weight:600;margin-top:3px}
.up{color:var(--green)}.down{color:var(--red)}
/* results feed */
.daygroup{margin-bottom:22px}
.dayh{font-size:13px;font-weight:700;color:var(--mut);letter-spacing:.04em;margin:0 4px 10px;text-transform:uppercase}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.mcard{background:var(--surface);border-radius:14px;box-shadow:var(--shadow);padding:13px 16px;font-size:14px;border-left:3px solid transparent}
.mcard.ft{border-left-color:var(--g2)}
.mcard.live{border-left-color:var(--live)}
.mcard .top{display:flex;justify-content:space-between;color:var(--mut);font-size:11px;margin-bottom:8px}
.mcard .st{font-weight:700}
.mcard .st.ft{color:var(--g2)}.mcard .st.live{color:var(--live)}
.mrow{display:flex;align-items:center;gap:8px;padding:3px 0}
.mrow .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mrow .sc{font-weight:700;font-variant-numeric:tabular-nums;font-size:16px}
.mrow.win .nm{font-weight:700}.mrow.lose{color:var(--mut)}
/* group tables */
.ggrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px}
.gcard{background:var(--surface);border-radius:var(--radius);box-shadow:var(--shadow);padding:16px 18px}
.gcard h3{font-size:13px;font-weight:700;color:var(--mut);letter-spacing:.05em;margin-bottom:10px;display:flex;justify-content:space-between}
.gt{width:100%;border-collapse:collapse;font-size:13px}
.gt th{color:var(--mut);font-size:10px;text-transform:uppercase;letter-spacing:.04em;text-align:right;padding:4px 5px;font-weight:600}
.gt th:first-child{text-align:left}
.gt td{padding:6px 5px;border-top:1px solid var(--hair);text-align:right;font-variant-numeric:tabular-nums}
.gt td:first-child{text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:140px}
.gt tr.q1 td:first-child{box-shadow:inset 3px 0 var(--green)}
.gt tr.q2 td:first-child{box-shadow:inset 3px 0 var(--blue)}
.gt .adv{font-weight:700}
.gt .chip{font-size:9.5px;font-weight:700;border-radius:6px;padding:1px 6px;margin-left:5px}
.chip.thru{color:#fff;background:var(--green)}.chip.out{color:var(--mut);background:var(--track)}
.gt .pn{color:var(--mut);width:14px}
.barmini{height:5px;border-radius:3px;background:var(--track);overflow:hidden;min-width:46px;display:inline-block;vertical-align:middle}
.barmini i{display:block;height:100%;background:linear-gradient(90deg,var(--g1),var(--g2))}
/* odds */
.card{background:var(--surface);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden}
.tscroll{overflow-x:auto}
table.big{width:100%;border-collapse:collapse;font-size:14px}
table.big th{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.05em;text-align:right;padding:13px 14px;border-bottom:1px solid var(--hair);white-space:nowrap}
table.big th:nth-child(-n+2){text-align:left}
table.big td{padding:11px 14px;border-bottom:1px solid var(--hair);text-align:right;font-variant-numeric:tabular-nums}
table.big td:nth-child(-n+2){text-align:left}
table.big tr:last-child td{border-bottom:none}
table.big tbody tr:hover{background:var(--tint)}
.teamcell{display:flex;align-items:center;gap:8px;white-space:nowrap}
.delta{font-size:11.5px;font-weight:700}
.champbar{display:inline-block;height:8px;border-radius:4px;background:var(--track);width:90px;overflow:hidden;vertical-align:middle;margin-right:8px}
.champbar i{display:block;height:100%;background:var(--tri)}
/* bracket */
.bwrap{width:100vw;margin-left:calc(50% - 50vw);overflow-x:auto;padding:8px 0 16px}
.bracket{display:flex;gap:12px;min-width:1280px;max-width:1460px;margin:0 auto;padding:0 22px;align-items:stretch}
.bcol{display:flex;flex-direction:column;flex:1;min-width:132px}
.bcol h4{text-align:center;color:var(--mut);font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;height:16px;margin-bottom:8px}
.ties{flex:1;display:flex;flex-direction:column;justify-content:space-around}
.tie{background:var(--surface);border-radius:12px;box-shadow:var(--shadow);overflow:hidden;font-size:12.5px;margin:4px 0}
.tie .mn{font-size:10px;color:var(--mut);padding:4px 10px 0}
.tie .row{display:flex;align-items:center;gap:6px;padding:5px 10px}
.tie .row:last-child{padding-bottom:7px}
.tie .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--mut)}
.tie .pc{color:var(--mut);font-variant-numeric:tabular-nums;font-size:11px}
.tie .row.w .nm{font-weight:650;color:var(--txt)}.tie .row.w .pc{color:var(--blue);font-weight:650}
.tie .row.w{background:var(--blue-soft)}
.tie.done .mn{color:var(--g2);font-weight:700}
.finalcol .tie{box-shadow:var(--shadow-lg);border:2px solid transparent;background:linear-gradient(var(--surface),var(--surface)) padding-box,var(--tri) border-box}
.note{color:var(--mut);font-size:13px;text-align:center;max-width:760px;margin:14px auto 0;background:var(--surface);border-radius:999px;padding:10px 22px;box-shadow:var(--shadow)}
.spin{display:inline-block;width:14px;height:14px;border:2px solid var(--track);border-top-color:var(--blue);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.mcard.clk{cursor:pointer;transition:transform .2s,box-shadow .2s}
.mcard.clk:hover{transform:translateY(-2px);box-shadow:var(--shadow-lg)}
.wpchip{display:inline-block;font-size:9.5px;font-weight:700;color:var(--blue);background:var(--blue-soft);border-radius:6px;padding:1px 6px;margin-left:6px}
/* win-prob modal */
.ov{position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.5);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
 display:none;align-items:center;justify-content:center;padding:18px}
.ov.show{display:flex}
.modal{background:var(--bg);border-radius:22px;box-shadow:var(--shadow-lg);max-width:880px;width:100%;max-height:94vh;overflow:auto;padding:22px 24px 26px}
.modal .mh{display:flex;align-items:center;justify-content:center;gap:14px;text-align:center;flex-wrap:wrap;position:relative}
.modal .mh .sc{font-size:34px;font-weight:800;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.modal .mh .tn{font-size:19px;font-weight:600}
.modal .close{position:absolute;right:-6px;top:-6px;border:none;background:var(--surface);box-shadow:var(--shadow);
 width:34px;height:34px;border-radius:50%;font-size:17px;cursor:pointer;color:var(--mut)}
.modal .meta{text-align:center;color:var(--mut);font-size:13px;margin:4px 0 12px}
.wpreadout{display:flex;gap:10px;justify-content:center;margin:6px 0 10px;flex-wrap:wrap}
.wpr{background:var(--surface);border-radius:12px;box-shadow:var(--shadow);padding:8px 14px;min-width:104px;text-align:center}
.wpr .v{font-size:21px;font-weight:700;font-variant-numeric:tabular-nums}
.wpr .k{font-size:11px;color:var(--mut)}
.wpr.h .v{color:var(--g2)}.wpr.a .v{color:var(--g3)}.wpr.d .v{color:var(--mut)}
.chartbox{background:var(--surface);border-radius:16px;box-shadow:var(--shadow);padding:10px 8px 4px;margin-top:6px}
.chartbox svg{width:100%;height:auto;display:block}
.gridln{stroke:var(--hair);stroke-width:1}
.axt{fill:var(--mut);font-size:11px}
.lblnow{fill:var(--mut);font-size:11px}
.ctrls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:center;margin-top:14px}
.ctrls .seg{display:flex;gap:6px;align-items:center;background:var(--surface);border-radius:999px;box-shadow:var(--shadow);padding:5px 8px}
.ctrls button{font-family:inherit;cursor:pointer;border:none;border-radius:999px;padding:7px 14px;font-size:13px;font-weight:600;background:var(--blue-soft);color:var(--blue)}
.ctrls button.solid{background:var(--blue);color:#fff}
.ctrls button.gh{background:var(--surface);box-shadow:var(--shadow);color:var(--g2)}
.ctrls button.ga{background:var(--surface);box-shadow:var(--shadow);color:var(--g3)}
.minrow{display:flex;align-items:center;gap:12px;justify-content:center;margin-top:12px}
.minrow input[type=range]{width:min(560px,80vw);accent-color:var(--blue)}
.minrow .mm{font-variant-numeric:tabular-nums;font-weight:700;min-width:42px}
.evchips{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-top:10px}
.evchip{font-size:11.5px;font-weight:600;border-radius:999px;padding:3px 10px;cursor:pointer;box-shadow:var(--shadow);background:var(--surface)}
.evchip.h{color:var(--g2)}.evchip.a{color:var(--g3)}
.evchip:hover{text-decoration:line-through;opacity:.7}
.modal .hint{text-align:center;color:var(--mut);font-size:12px;margin-top:10px}
footer{margin-top:80px;padding:26px 22px 0;border-top:1px solid var(--hair);color:var(--mut);font-size:12px;text-align:center;line-height:1.8}
@media(max-width:640px){.hero h1{font-size:32px}}
</style>
</head>
<body>
<nav><div class="in"><b><span class="lg">26</span> World Cup 26</b>
<a href="index.html">Forecast</a><a href="#feed" class="on">Live</a><a href="#groups">Groups</a><a href="#odds">Title odds</a><a href="#bracket">Bracket</a></div></nav>
<div class="wrap">

<header class="hero">
 <div class="livetag"><span class="pulse"></span>LIVE · AUTO-UPDATING</div>
 <h1>The tournament, <span class="grad">recomputed in real time.</span></h1>
 <div class="statusbar" id="statusbar"></div>
 <div class="bigstat" id="bigstat"></div>
</header>

<section id="feed">
 <div class="shead"><h2>Results &amp; fixtures</h2><p>Final scores pulled live; upcoming kickoffs in your local time. Each completed match instantly reshapes every probability below.</p></div>
 <div id="feedbox"></div>
</section>

<section id="groups">
 <div class="shead"><h2>Live group standings</h2><p>Actual points and goal difference so far, with each team's live chance of reaching the knockouts — recomputed from the model conditioned on results played.</p></div>
 <div class="ggrid" id="ggrid"></div>
</section>

<section id="odds">
 <div class="shead"><h2>Live title odds</h2><p>Champion and round-by-round probabilities, updating with every result. Δ shows the swing since the pre-tournament forecast.</p></div>
 <div class="card tscroll"><table class="big" id="oddstable">
  <thead><tr><th>#</th><th>Team</th><th>Champion</th><th>Δ</th><th>Final</th><th>Semis</th><th>Quarters</th><th>R16</th><th>Advance</th></tr></thead>
  <tbody></tbody></table></div>
</section>

<section id="bracket">
 <div class="shead"><h2>Projected bracket</h2><p>The current most-likely path given results so far — favourites advancing each tie, with live win probabilities. Completed knockout matches lock in automatically.</p></div>
 <div class="bwrap"><div class="bracket" id="btree"></div></div>
 <div class="note" id="bracketnote"></div>
</section>

<footer>
 Live engine runs entirely in your browser: <span id="ftN"></span> Monte-Carlo tournaments per refresh, conditioned on real results fetched from the open match database.<br>
 Pre-tournament model: penalised Dixon-Coles (ξ=0.7/yr) ⊗ World Football Elo · Bracket &amp; Annex C: FIFA regulations.<br>
 Unofficial fan analytics project — not affiliated with or endorsed by FIFA. Remaining-match probabilities use the pre-tournament model; played results are locked in.
</footer>
</div>

<div class="ov" id="wpov"><div class="modal" id="wpmodal"></div></div>

<script>
const D = __DATA__;
const FEED = "__FEED__";
const NSIMS = 20000;
__ENGINE__
__INPLAY__
</script>
<script>
const F=t=>D.flags[t]||"";
const pc=(x,d=0)=>(100*x).toFixed(d)+"%";
const fmtTime=new Intl.DateTimeFormat(undefined,{hour:"numeric",minute:"2-digit"});
const fmtDay=new Intl.DateTimeFormat(undefined,{weekday:"short",month:"short",day:"numeric"});
const fmtDayLong=new Intl.DateTimeFormat(undefined,{weekday:"long",month:"long",day:"numeric"});
const fmtDayKey=new Intl.DateTimeFormat("en-CA",{year:"numeric",month:"2-digit",day:"2-digit"});
const TZ=Intl.DateTimeFormat().resolvedOptions().timeZone||"local time";
const tzAbbr=(()=>{try{return new Intl.DateTimeFormat("en-US",{timeZoneName:"short"}).formatToParts(new Date()).find(p=>p.type==="timeZoneName").value;}catch(e){return"";}})();

const fixByPair={}; D.fixtures.forEach(f=>fixByPair[f.home+"|"+f.away]=f.id);
const fixById={}; D.fixtures.forEach(f=>fixById[f.id]=f);
const groupOf={}; for(const g of D.group_order) for(const t of D.groups[g]) groupOf[t]=g;

let STATE={results:{},ko:{},source:"snapshot",fetchedUTC:null,played:0};

/* ---- parse the live CSV feed ---- */
function parseCSV(text){
 const lines=text.split(/\r?\n/).filter(x=>x); const head=lines[0].split(",");
 const ix=n=>head.indexOf(n);
 const di=ix("date"),hi=ix("home_team"),ai=ix("away_team"),hsi=ix("home_score"),asi=ix("away_score"),ti=ix("tournament");
 const out=[];
 for(let i=1;i<lines.length;i++){ // naive split ok: no quoted commas in this dataset
  const c=lines[i].split(",");
  if(c[ti]!=="FIFA World Cup") continue;
  if(c[di]<"2026-06-01") continue;
  out.push({date:c[di],home:c[hi],away:c[ai],hs:c[hsi],as:c[asi]});
 }
 return out;
}
function ingest(rows){
 const results={},ko={};
 rows.forEach(r=>{
  if(r.hs===""||r.hs==null||isNaN(+r.hs)) return;
  const id=fixByPair[r.home+"|"+r.away];
  if(id!=null){ results[id]=[+r.hs,+r.as]; }
  // knockout games (date>=06-28) handled once groups complete (mapped later)
 });
 return {results,ko};
}

async function loadLive(){
 setStatus("loading");
 try{
  const res=await fetch(FEED,{cache:"no-store"});
  if(!res.ok) throw new Error("HTTP "+res.status);
  const txt=await res.text();
  const rows=parseCSV(txt);
  const {results,ko}=ingest(rows);
  STATE={results,ko,source:"live",fetchedUTC:new Date(),played:Object.keys(results).length};
 }catch(e){
  // fallback to embedded snapshot
  const results={};
  D.snapshot.forEach(s=>{const id=fixByPair[s.home+"|"+s.away]; if(id!=null)results[id]=[s.hs,s["as"]];});
  STATE={results,ko:{},source:"snapshot",fetchedUTC:new Date(),played:Object.keys(results).length,err:String(e.message||e)};
 }
 recompute();
}

/* ---- run the Monte Carlo + render ---- */
let LAST=null;
function recompute(){
 setStatus("sim");
 setTimeout(()=>{                       // let the spinner paint
  const out=WCLive.runLive(D,{N:NSIMS,results:STATE.results,ko:STATE.ko});
  LAST=out;
  renderStatus(); renderBig(out); renderFeed(); renderGroups(out); renderOdds(out); renderBracket(out);
 },20);
}

/* ---- status bar ---- */
let statusMode="idle";
function setStatus(m){statusMode=m;renderStatus();}
function renderStatus(){
 const sb=document.getElementById("statusbar");
 const srcDot=STATE.source==="live"?'<span class="dot ok"></span>':'<span class="dot warn"></span>';
 const srcTxt=STATE.source==="live"?'<b>Live feed</b> connected':'<b>Offline snapshot</b> (feed blocked)';
 const upd=STATE.fetchedUTC?fmtTime.format(STATE.fetchedUTC):"—";
 const busy=statusMode==="sim"?'<span class="pill"><span class="spin"></span> simulating '+NSIMS.toLocaleString()+' tournaments…</span>'
           :statusMode==="loading"?'<span class="pill"><span class="spin"></span> fetching results…</span>':'';
 sb.innerHTML=
  `<span class="pill">${srcDot}${srcTxt}</span>`+
  `<span class="pill"><b>${STATE.played}</b>/72 group matches played</span>`+
  `<span class="pill">updated <b>${upd}</b> · ${tzAbbr}</span>`+
  busy+
  `<button class="btn ghost" id="refreshBtn">↻ Refresh now</button>`+
  `<button class="btn" id="autoBtn"></button>`;
 document.getElementById("refreshBtn").onclick=loadLive;
 const ab=document.getElementById("autoBtn"); ab.textContent=AUTO?"⏸ Auto: on":"▶ Auto: off";
 ab.onclick=()=>{AUTO=!AUTO; if(AUTO)scheduleAuto(); renderStatus();};
}

/* ---- big stat cards ---- */
function renderBig(out){
 const champ=Object.entries(out.champion).sort((a,b)=>b[1]-a[1]);
 const [c1,c2]=champ;
 const mover=Object.entries(out.champion).map(([t,p])=>[t,p-D.baseline[t].p_champion])
   .sort((a,b)=>Math.abs(b[1])-Math.abs(a[1]))[0];
 const nextGame=upcoming()[0];
 const d1=c1[1]-D.baseline[c1[0]].p_champion;
 document.getElementById("bigstat").innerHTML=[
  ["Current favourite",`${F(c1[0])} ${c1[0]}`,pc(c1[1],1),deltaHTML(d1)],
  ["Second favourite",`${F(c2[0])} ${c2[0]}`,pc(c2[1],1),deltaHTML(c2[1]-D.baseline[c2[0]].p_champion)],
  ["Biggest mover",`${F(mover[0])} ${mover[0]}`,(mover[1]>=0?"+":"")+pc(mover[1],1).replace("%","")+" pts",deltaHTML(mover[1])],
  ["Next kickoff", nextGame?`${F(nextGame.home)} v ${F(nextGame.away)}`:"—", nextGame?fmtTime.format(new Date(nextGame.utc)):"—", nextGame?fmtDay.format(new Date(nextGame.utc)):""],
 ].map(c=>`<div class="bs"><div class="k">${c[0]}</div><div class="v">${c[2]}</div><div style="font-weight:600;font-size:14px;margin-top:2px">${c[1]}</div><div class="d">${c[3]}</div></div>`).join("");
}
function deltaHTML(d){ if(Math.abs(d)<0.0005) return '<span style="color:var(--mut)">no change</span>';
 const c=d>0?"up":"down",a=d>0?"▲":"▼"; return `<span class="delta ${c}">${a} ${pc(Math.abs(d),1)}</span>`; }

/* ---- feed ---- */
function upcoming(){ const now=Date.now();
 return D.fixtures.filter(f=>f.utc && !STATE.results[f.id] && new Date(f.utc).getTime()>now-2*3600e3)
  .sort((a,b)=>new Date(a.utc)-new Date(b.utc)); }
function renderFeed(){
 const now=Date.now();
 const items=D.fixtures.map(f=>{
  const r=STATE.results[f.id]; const t=f.utc?new Date(f.utc).getTime():null;
  let status= r?"ft":(t&&now>=t&&now<t+2.5*3600e3?"live":"upcoming");
  return {f,r,t,status,key:f.utc?fmtDayKey.format(new Date(f.utc)):f.id};
 }).sort((a,b)=>(a.t||0)-(b.t||0));
 const byDay={};
 items.forEach(it=>{(byDay[it.key]=byDay[it.key]||[]).push(it);});
 const today=fmtDayKey.format(new Date());
 const box=document.getElementById("feedbox"); box.innerHTML="";
 Object.keys(byDay).sort().forEach(k=>{
  const its=byDay[k]; const d=its[0].f.utc?new Date(its[0].f.utc):null;
  const label=d?fmtDayLong.format(d)+(k===today?" · TODAY":""):"";
  const cards=its.map(({f,r,status})=>{
   const time=f.utc?fmtTime.format(new Date(f.utc)):"";
   const stTxt=status==="ft"?"FULL TIME":status==="live"?"● LIVE":time;
   const rowsHTML=[[f.home,r?r[0]:null],[f.away,r?r[1]:null]].map(([t,sc],i)=>{
     const other=r?r[1-i]:null; const cls=r?(sc>other?"win":sc<other?"lose":""):"";
     return `<div class="mrow ${cls}"><span>${F(t)}</span><span class="nm">${t}</span><span class="sc">${sc==null?"":sc}</span></div>`;
   }).join("");
   return `<div class="mcard clk ${status}" data-fid="${f.id}"><div class="top"><span>Group ${f.group} · ${f.city}</span><span class="st ${status}">${stTxt}</span></div>${rowsHTML}<div style="text-align:right;margin-top:5px"><span class="wpchip">📈 WIN PROBABILITY</span></div></div>`;
  }).join("");
  box.insertAdjacentHTML("beforeend",`<div class="daygroup"><div class="dayh">${label}</div><div class="mgrid">${cards}</div></div>`);
 });
}

/* ---- groups ---- */
function renderGroups(out){
 const box=document.getElementById("ggrid"); box.innerHTML="";
 for(const g of D.group_order){
  const tbl=WCLive.liveTable(D,g,STATE.results);
  const rows=tbl.map((o,i)=>{
   const adv=out.r32[o.team];
   const chip = adv>0.995?'<span class="chip thru">THRU</span>':adv<0.005?'<span class="chip out">OUT</span>':"";
   const qcls=i===0?"q1":i===1?"q2":"";
   return `<tr class="${qcls}"><td><span class="pn">${i+1}</span> ${F(o.team)} ${o.team}${chip}</td>
    <td>${o.pld}</td><td>${o.pts}</td><td>${o.gd>=0?'+':''}${o.gd}</td>
    <td class="adv"><span class="barmini"><i style="width:${100*adv}%"></i></span> ${pc(adv)}</td></tr>`;
  }).join("");
  const played=tbl.reduce((s,o)=>s+o.pld,0)/2;
  box.insertAdjacentHTML("beforeend",
   `<div class="gcard"><h3><span>GROUP ${g}</span><span>${played}/6 played</span></h3>
    <table class="gt"><thead><tr><th>Team</th><th>Pld</th><th>Pts</th><th>GD</th><th>Advance</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`);
 }
}

/* ---- odds table ---- */
function renderOdds(out){
 const rows=Object.keys(out.champion).map(t=>({t,...out})).map(o=>({
   team:o.t,champ:out.champion[o.t],fin:out.final[o.t],sf:out.sf[o.t],qf:out.qf[o.t],r16:out.r16[o.t],r32:out.r32[o.t],
   d:out.champion[o.t]-D.baseline[o.t].p_champion}))
  .sort((a,b)=>b.champ-a.champ);
 const tb=document.querySelector("#oddstable tbody");
 tb.innerHTML=rows.map((r,i)=>`<tr>
  <td>${i+1}</td>
  <td><div class="teamcell">${F(r.team)} ${r.team}</div></td>
  <td><span class="champbar"><i style="width:${Math.min(100,100*r.champ/0.20)}%"></i></span><b>${pc(r.champ,1)}</b></td>
  <td>${deltaHTML(r.d)}</td>
  <td>${pc(r.fin,1)}</td><td>${pc(r.sf)}</td><td>${pc(r.qf)}</td><td>${pc(r.r16)}</td><td>${pc(r.r32)}</td>
 </tr>`).join("");
}

/* ---- projected bracket (deterministic, from live results + model) ---- */
function projStrength(t){return D.baseline[t].p_champion;}
function projectStandings(out){
 const winners={},runners={},thirds={},thirdScore={};
 for(const g of D.group_order){
  const tbl=WCLive.liveTable(D,g,STATE.results);   // current actual order
  // refine undecided ordering using model strength while respecting points
  const ord=tbl.slice().sort((a,b)=>(b.pts-a.pts)||(b.gd-a.gd)||(b.gf-a.gf)||(projStrength(b.team)-projStrength(a.team)));
  winners[g]=ord[0].team; runners[g]=ord[1].team; thirds[g]=ord[2].team;
  thirdScore[g]=ord[2].pts*1000+ord[2].gd*10+projStrength(ord[2].team);
 }
 const qualG=D.group_order.split("").sort((a,b)=>thirdScore[b]-thirdScore[a]).slice(0,8).sort();
 const slotGroups=D.annex[qualG.join("")];
 const thirdForSlot={}; D.third_slots.forEach((s,i)=>thirdForSlot[s]=thirds[slotGroups[i]]);
 return {winners,runners,thirds,thirdForSlot,qualG};
}
function koP(t1,t2,venue){
 const i1=D.teams.indexOf(t1),i2=D.teams.indexOf(t2),hosts=D.hosts;
 if(hosts.includes(t1)&&t1===venue) return D.P1[i1][i2];
 if(hosts.includes(t2)&&t2===venue) return 1-D.P1[i2][i1];
 return D.P0[i1][i2];
}
function renderBracket(out){
 const S=projectStandings(out);
 const teamOf=(code,info)=> code==="3rd"?S.thirdForSlot[info.third_slot]:(code[0]==="1"?S.winners:S.runners)[code[1]];
 const M={};   // matchNo -> {t1,t2,p1,winner,venue,done}
 for(const mno in D.ko_struct.r32){const info=D.ko_struct.r32[mno];
  const t1=teamOf(info.home,info),t2=teamOf(info.away,info);
  build(mno,t1,t2,info.venue_country);}
 for(const rk of ["r16","qf","sf","final"]){const st=D.ko_struct[rk];
  for(const mno in st){const [m1,m2,venue]=st[mno]; build(mno,M[m1].winner,M[m2].winner,venue);}}
 function build(mno,t1,t2,venue){
  const act=STATE.ko[mno];
  const p=koP(t1,t2,venue); const win=act||(p>=0.5?t1:t2);
  M[mno]={t1,t2,p1:p,winner:win,venue,done:!!act};
 }
 const kt=D.ko_times;
 function tie(mno){const m=M[mno]; const rows=[[m.t1,m.p1],[m.t2,1-m.p1]];
  const k=kt[mno]; const lp=k?new Date(k.utc):null;
  const meta=`M${mno}`+(lp?` · ${fmtDay.format(lp)}, ${fmtTime.format(lp)}`:"")+(k?` · ${k.city}`:"");
  return `<div class="tie ${m.done?"done":""}"><div class="mn">${meta}${m.done?" · FT":""}</div>`+
   rows.map(([t,p])=>`<div class="row ${t===m.winner?"w":""}"><span>${F(t)}</span><span class="nm">${t}</span><span class="pc">${m.done?(t===m.winner?"✓":""):pc(p)}</span></div>`).join("")+`</div>`;
 }
 const cols=[["Round of 32",[74,77,73,75,83,84,81,82]],["Round of 16",[89,90,93,94]],["Quarterfinals",[97,98]],["Semifinal",[101]],
  ["Final",[104]],["Semifinal",[102]],["Quarterfinals",[99,100]],["Round of 16",[91,92,95,96]],["Round of 32",[76,78,79,80,86,88,85,87]]];
 document.getElementById("btree").innerHTML=cols.map(([h,ms])=>
  `<div class="bcol ${ms[0]===104?"finalcol":""}"><h4>${h}</h4><div class="ties">`+ms.map(n=>tie(""+n)).join("")+`</div></div>`).join("");
 const champ=M["104"].winner;
 document.getElementById("bracketnote").innerHTML=
  STATE.played<72?`Projection updates as groups finish · current projected champion: <b>${F(champ)} ${champ}</b>`
                 :`Groups complete · knockout results lock in as matches finish`;
}

/* ---- auto refresh ---- */
let AUTO=true, autoTimer=null;
function scheduleAuto(){ clearTimeout(autoTimer); if(!AUTO)return;
 autoTimer=setTimeout(()=>{loadLive().then(scheduleAuto);},90000); }

document.getElementById("ftN").textContent=NSIMS.toLocaleString();
loadLive().then(scheduleAuto);

/* ===== Win-probability explorer ===== */
const WP={fid:null,events:[],minute:90,anim:null,mode:"actual"};
const ov=document.getElementById("wpov"), modalEl=document.getElementById("wpmodal");
function mulberry(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}

function openMatch(fid){
 const f=fixById[fid]; if(!f) return;
 WP.fid=fid; stopAnim();
 const res=STATE.results[fid];
 const known=D.goal_events[f.home+"|"+f.away];
 if(res && known){ WP.events=known.map(e=>({...e})); WP.mode="actual"; WP.minute=90; }
 else if(res){ // played but goal minutes unknown: place final-score goals at spread minutes
   WP.events=spreadGoals(res[0],res[1]); WP.mode="actual"; WP.minute=90; }
 else { WP.events=WCInPlay.simulateStory(f.eh,f.ea,mulberry(fid*2654435761>>>0)); WP.mode="sim"; WP.minute=0; }
 ov.classList.add("show"); document.body.style.overflow="hidden";
 drawModal();
 if(!res) animatePlay();        // auto-play the simulated story for upcoming games
}
function spreadGoals(h,a){const ev=[];const tot=h+a;let i=0;
 for(let k=0;k<h;k++)ev.push({min:Math.round((++i)*90/(tot+1)),team:"home"});
 for(let k=0;k<a;k++)ev.push({min:Math.round((++i)*90/(tot+1)),team:"away"});
 return ev.sort((x,y)=>x.min-y.min);}
function closeModal(){ov.classList.remove("show");document.body.style.overflow="";stopAnim();}
ov.addEventListener("click",e=>{if(e.target===ov)closeModal();});
addEventListener("keydown",e=>{if(e.key==="Escape")closeModal();});

function xMap(m){return 52+(m/90)*(1000-52-72);}
function yMap(p){return 18+(1-p)*(360-18-30);}
function buildChart(f){
 const T=WCInPlay.timeline(f.eh,f.ea,WP.events);
 const line=(sel)=>T.map(pt=>xMap(pt.m)+","+yMap(pt.p[sel])).join(" ");
 const grid=[0,.25,.5,.75,1].map(v=>`<line class="gridln" x1="52" y1="${yMap(v)}" x2="928" y2="${yMap(v)}"/><text class="axt" x="44" y="${yMap(v)+4}" text-anchor="end">${v*100|0}%</text>`).join("");
 const xt=[1,15,30,45,60,75,90].map(m=>`<text class="axt" x="${xMap(m)}" y="352" text-anchor="middle">${m}'</text>`).join("");
 const goals=WP.events.map(e=>`<line x1="${xMap(e.min)}" y1="18" x2="${xMap(e.min)}" y2="330" stroke="${e.team==='home'?'var(--g2)':'var(--g3)'}" stroke-width="1" stroke-dasharray="2 3" opacity=".5"/>
  <circle cx="${xMap(e.min)}" cy="14" r="3.2" fill="${e.team==='home'?'var(--g2)':'var(--g3)'}"/>`).join("");
 const nowX=xMap(WP.minute);
 const cur=T[WP.minute].p;
 const nowMarks=`<line x1="${nowX}" y1="14" x2="${nowX}" y2="330" stroke="var(--txt)" stroke-width="1.5" opacity=".5"/>`+
  [[0,'var(--g2)'],[1,'#9aa3b2'],[2,'var(--g3)']].map(([s,c])=>`<circle cx="${nowX}" cy="${yMap(cur[s])}" r="4" fill="${c}" stroke="var(--surface)" stroke-width="1.5"/>`).join("");
 const endLbl=(sel,c,txt)=>{const p=T[T.length-1].p[sel];return `<text x="934" y="${yMap(p)+4}" class="axt" fill="${c}" font-weight="700">${txt}</text>`;};
 return `<svg viewBox="0 0 1000 360" preserveAspectRatio="xMidYMid meet">
  ${grid}${xt}${goals}
  <polyline fill="none" stroke="#9aa3b2" stroke-width="2" stroke-dasharray="5 4" points="${line(1)}"/>
  <polyline fill="none" stroke="var(--g3)" stroke-width="2.5" points="${line(2)}"/>
  <polyline fill="none" stroke="var(--g2)" stroke-width="2.5" points="${line(0)}"/>
  ${nowMarks}
  ${endLbl(0,'var(--g2)','H')}${endLbl(1,'#9aa3b2','D')}${endLbl(2,'var(--g3)','A')}
 </svg>`;
}
function drawModal(){
 const f=fixById[WP.fid]; const T=WCInPlay.timeline(f.eh,f.ea,WP.events);
 const [gh,ga]=WCInPlay.scoreAt(WP.events,WP.minute);
 const cur=T[WP.minute].p;
 const res=STATE.results[WP.fid];
 const statusTxt = WP.mode==="sim" ? "Simulated match story — press ▶ or scrub the minute" :
   (res?`Full time · actual goal timeline`:"");
 const kt=f.utc?new Date(f.utc):null;
 modalEl.innerHTML=`
  <button class="close" id="wpclose">✕</button>
  <div class="mh"><span class="tn">${F(f.home)} ${f.home}</span><span class="sc">${gh} – ${ga}</span><span class="tn">${f.away} ${F(f.away)}</span></div>
  <div class="meta">Group ${f.group} · ${f.city}${kt?" · "+fmtDay.format(kt):""} · model xG ${f.eh.toFixed(2)}–${f.ea.toFixed(2)} · <b style="color:var(--blue)">${statusTxt}</b></div>
  <div class="wpreadout">
   <div class="wpr h"><div class="v">${pc(cur[0],1)}</div><div class="k">${f.home} win</div></div>
   <div class="wpr d"><div class="v">${pc(cur[1],1)}</div><div class="k">Draw</div></div>
   <div class="wpr a"><div class="v">${pc(cur[2],1)}</div><div class="k">${f.away} win</div></div>
  </div>
  <div class="chartbox">${buildChart(f)}</div>
  <div class="minrow"><span class="mm">${WP.minute}'</span>
   <input type="range" id="wpmin" min="0" max="90" value="${WP.minute}"></div>
  <div class="ctrls">
   <div class="seg"><button class="solid" id="wpplay">▶ Play</button><button id="wprewind">↺</button></div>
   <div class="seg"><button class="gh" id="wpgh">＋ ${f.home} goal @${WP.minute}'</button><button class="ga" id="wpga">＋ ${f.away} goal @${WP.minute}'</button></div>
   <div class="seg">${res?`<button id="wpactual">Actual story</button>`:`<button id="wpsim">🎲 Simulate again</button>`}<button id="wpclear">Clear goals</button></div>
  </div>
  ${WP.events.length?`<div class="evchips">`+WP.events.map((e,i)=>`<span class="evchip ${e.team}" data-i="${i}">${e.min}' ${e.team==='home'?F(f.home)+' '+f.home:F(f.away)+' '+f.away} ✕</span>`).join("")+`</div>`:""}
  <div class="hint">Remaining-time goals modelled as Poisson(xG × time left) — exact in-play win probability. Click a goal chip to remove it; add goals or scrub the minute to explore.</div>`;
 // wire
 document.getElementById("wpclose").onclick=closeModal;
 const mr=document.getElementById("wpmin");
 mr.oninput=()=>{WP.minute=+mr.value;stopAnim();drawModal();};
 document.getElementById("wpplay").onclick=animateToggle;
 document.getElementById("wprewind").onclick=()=>{WP.minute=0;stopAnim();drawModal();};
 document.getElementById("wpgh").onclick=()=>{addGoal("home");};
 document.getElementById("wpga").onclick=()=>{addGoal("away");};
 document.getElementById("wpclear").onclick=()=>{WP.events=[];stopAnim();drawModal();};
 const sb=document.getElementById("wpsim"); if(sb) sb.onclick=()=>{WP.events=WCInPlay.simulateStory(f.eh,f.ea,Math.random);WP.minute=0;stopAnim();drawModal();animatePlay();};
 const ab=document.getElementById("wpactual"); if(ab) ab.onclick=()=>{const k=D.goal_events[f.home+"|"+f.away]||spreadGoals(res[0],res[1]);WP.events=k.map(e=>({...e}));WP.minute=90;stopAnim();drawModal();};
 [...modalEl.querySelectorAll(".evchip")].forEach(c=>c.onclick=()=>{WP.events.splice(+c.dataset.i,1);drawModal();});
}
function addGoal(team){WP.events.push({min:WP.minute,team});WP.events.sort((a,b)=>a.min-b.min);drawModal();}
let animTimer=null;
function stopAnim(){if(animTimer){clearInterval(animTimer);animTimer=null;const b=document.getElementById("wpplay");if(b)b.textContent="▶ Play";}}
function animateToggle(){ if(animTimer){stopAnim();return;} animatePlay(); }
function animatePlay(){ stopAnim(); if(WP.minute>=90)WP.minute=0; const b=document.getElementById("wpplay");if(b)b.textContent="⏸ Pause";
 animTimer=setInterval(()=>{ WP.minute+=1; if(WP.minute>=90){WP.minute=90;drawModal();stopAnim();return;} drawModal(); },55); }

document.getElementById("feedbox").addEventListener("click",e=>{const c=e.target.closest(".mcard.clk");if(c)openMatch(+c.dataset.fid);});

/* nav highlight */
const secs=[...document.querySelectorAll("section")],links=[...document.querySelectorAll('nav a[href^="#"]')];
addEventListener("scroll",()=>{let cur="";for(const s of secs)if(scrollY>=s.offsetTop-90)cur=s.id;
 links.forEach(l=>l.classList.toggle("on",l.getAttribute("href")==="#"+cur));},{passive:true});
</script>
</body>
</html>"""

html = (HTML.replace("__DATA__", DATA)
            .replace("__ENGINE__", ENGINE)
            .replace("__INPLAY__", INPLAY)
            .replace("__FEED__", FEED_URL))
open("website/live.html", "w", encoding="utf-8").write(html)
print(f"website/live.html written ({len(html)/1024:.0f} KB)")
