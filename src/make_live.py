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
<meta name="theme-color" content="#f5f5f7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<meta name="description" content="Live 2026 World Cup forecast: in-play win probabilities, lineups, ratings, live stats and championship odds — re-simulated after every result and tracked against the market.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="World Cup 2026 — Live Forecast">
<meta property="og:title" content="World Cup 2026 — Live Forecast">
<meta property="og:description" content="In-play win probabilities, live stats and championship odds — every result re-simulates the tournament, tracked against the market.">
<meta property="og:image" content="https://airmiz.github.io/World-Cup-Prediction/og.png">
<meta property="og:url" content="https://airmiz.github.io/World-Cup-Prediction/live.html">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="World Cup 2026 — Live Forecast">
<meta name="twitter:description" content="In-play win probabilities and live stats, tracked against the market.">
<meta name="twitter:image" content="https://airmiz.github.io/World-Cup-Prediction/og.png">
<script>if("serviceWorker" in navigator)addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){})});</script>
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
/* stats */
.stwrap{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.stwrap{grid-template-columns:1fr}}
.stcard{background:var(--surface);border-radius:var(--radius);box-shadow:var(--shadow);padding:16px 18px}
.stcard h3{font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--mut);margin-bottom:12px;display:flex;align-items:center;gap:8px}
.lbrow{display:flex;align-items:center;gap:10px;padding:7px 0;font-size:14px;border-top:1px solid var(--hair)}
.lbrow:first-of-type{border-top:none}
.lbrow .rk{width:18px;color:var(--mut);font-weight:700;font-size:12px;text-align:center}
.lbrow .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lbrow .big{font-weight:800;font-variant-numeric:tabular-nums}
.lbrow .sub{color:var(--mut);font-size:11.5px}
.lbrow .gb{font-size:15px}
.lbrow.lead{background:linear-gradient(90deg,var(--blue-soft),transparent);border-radius:8px;margin:0 -8px;padding-left:8px;padding-right:8px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.tile{background:var(--bg);border-radius:12px;padding:14px;position:relative;overflow:hidden}
.tile::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--tri)}
.tile .k{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
.tile .v{font-size:20px;font-weight:800;margin-top:4px;letter-spacing:-.01em}
.tile .d{font-size:12px;color:var(--mut);margin-top:3px}
.ratemini{width:54px;height:6px;border-radius:3px;background:var(--track);overflow:hidden;display:inline-block;vertical-align:middle}
.ratemini i{display:block;height:100%;background:var(--tri)}
/* team modal */
#oddstable tbody tr{cursor:pointer}
.formchips{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}
.fchip{width:26px;height:26px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;color:#fff}
.fchip.W{background:var(--green)}.fchip.D{background:#aeaeb2}.fchip.L{background:var(--red)}
.frow{display:flex;align-items:center;gap:9px;font-size:13px;padding:5px 0;border-top:1px solid var(--hair)}
.frow:first-child{border-top:none}
.frow .res{width:22px;height:22px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;color:#fff;flex:none}
.frow .sc{font-variant-numeric:tabular-nums;font-weight:700}
.h2hrow{display:flex;align-items:center;gap:9px;font-size:13.5px;padding:6px 0;border-top:1px solid var(--hair)}
.h2hrow:first-child{border-top:none}
.h2hrow .opp{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.h2hrow .wdl{font-variant-numeric:tabular-nums;color:var(--mut)}
.tmstats{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:10px;margin:8px 0 4px}
.tmstats .b{background:var(--bg);border-radius:10px;padding:9px 11px;text-align:center}
.tmstats .b .v{font-size:18px;font-weight:800}.tmstats .b .k{font-size:10.5px;color:var(--mut);margin-top:2px}
/* score heatmap */
.heat{display:grid;gap:3px;margin-top:8px;max-width:360px}
.heatcell{aspect-ratio:1;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--txt);font-variant-numeric:tabular-nums}
.heatcell.act{outline:2.5px solid #f5c84b;font-weight:800}
.heatlbl{font-size:10px;color:var(--mut);display:flex;align-items:center;justify-content:center}
.heatcap{font-size:11px;color:var(--mut);margin-top:6px;text-align:center}
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
/* match centre */
.mc{margin-top:18px;display:grid;gap:14px}
.mcsec{background:var(--surface);border-radius:14px;box-shadow:var(--shadow);padding:14px 16px}
.scgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px}
.sctile{background:var(--surface);border-radius:14px;box-shadow:var(--shadow);padding:14px 16px;text-align:center}
.sctile .scv{font-size:26px;font-weight:900;color:var(--txt);font-variant-numeric:tabular-nums;line-height:1}
.sctile .scl{font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--mut);margin-top:6px}
.sctile .scs{font-size:10px;color:var(--mut);opacity:.8;margin-top:2px}
.mvk{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.mvkside .mvkh{font-size:11px;font-weight:800;color:var(--txt);margin-bottom:8px}
.scbar{display:grid;grid-template-columns:54px 1fr auto;gap:8px;align-items:center;margin:5px 0}
.scbar .scbl{font-size:10px;color:var(--mut);text-transform:uppercase;letter-spacing:.4px;font-weight:700}
.scbar .scbb{height:8px;background:var(--track);border-radius:4px;overflow:hidden}
.scbar .scbb i{display:block;height:100%;border-radius:4px;background:var(--mut);transition:width .4s ease}
.scbar .scbb i.win{background:var(--live)}
.scbar .scbv{font-size:12px;font-weight:700;font-variant-numeric:tabular-nums;color:var(--txt)}
.sctab td .pkpc{color:var(--mut);font-size:11px;font-variant-numeric:tabular-nums}
.sctab .okp{color:var(--live);font-weight:900}.sctab .nop{color:var(--amber);font-weight:900}
.wiftop{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:10px}
.wifhint{font-size:11px;color:var(--mut)}
.wifgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:8px 18px}
.wifgrp{padding:4px 0}
.wifgl{font-size:10px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);margin:6px 0 4px}
.wifrow{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center;padding:3px 0}
.wift{font-size:12px;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wift.a{text-align:right}
.wifbtns{display:flex;gap:3px}
.wifbtns button{width:26px;height:24px;border:1px solid var(--border);background:var(--surface);color:var(--mut);border-radius:6px;font-weight:800;font-size:11px;cursor:pointer;transition:.15s}
.wifbtns button:hover{border-color:var(--blue)}
.wifbtns button.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.wifimpact{margin-top:14px}
.wifcols{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.wifh{font-size:11px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;margin-bottom:8px}
.wifh.up{color:var(--live)}.wifh.dn{color:var(--amber)}
.wifm{display:flex;align-items:center;gap:7px;font-size:13px;padding:4px 0;border-bottom:1px solid var(--border)}
.wifm .wifd{margin-left:auto;font-weight:800;font-size:11px;font-variant-numeric:tabular-nums}
.wifm .wifd.up{color:var(--live)}.wifm .wifd.dn{color:var(--amber)}
.wifm .wifnow{font-weight:700;font-variant-numeric:tabular-nums;color:var(--mut);min-width:42px;text-align:right}
#pedibar{margin-top:10px}
.pedrow{display:grid;grid-template-columns:1fr 120px auto;gap:10px;align-items:center;margin:5px 0}
.pednm{font-size:12px;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pedbar{height:8px;background:var(--track);border-radius:4px;overflow:hidden}
.pedbar i{display:block;height:100%;border-radius:4px;background:linear-gradient(90deg,var(--blue),var(--live));transition:width .4s ease}
.pedv{font-size:13px;font-weight:800;font-variant-numeric:tabular-nums;color:var(--txt)}
.pedv .pedn{font-size:10px;font-weight:600;color:var(--mut)}
.mcsec h4{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.mcsec h4 .tag{font-size:9.5px;font-weight:600;color:var(--blue);background:var(--blue-soft);border-radius:6px;padding:2px 7px;text-transform:none;letter-spacing:0}
.golog{display:flex;flex-direction:column;gap:7px}
.gol{display:flex;align-items:center;gap:9px;font-size:13.5px}
.gol .mn{font-variant-numeric:tabular-nums;font-weight:700;color:var(--txt);min-width:34px}
.gol .ic{font-size:14px}
.gol .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gol .bdg{font-size:9.5px;font-weight:700;border-radius:6px;padding:1px 6px}
.bdg.og{color:var(--red);background:rgba(255,59,48,.12)}
.bdg.pen{color:var(--amber);background:rgba(255,159,10,.14)}
.rlist{display:flex;flex-direction:column;gap:2px}
.rteam{display:flex;align-items:center;gap:7px;font-size:11px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:var(--mut);margin:14px 0 6px;padding-bottom:5px;border-bottom:1px solid var(--hair)}
.rteam:first-child{margin-top:0}
.rteam .rtflag{font-size:15px}
.rrow{display:flex;align-items:center;gap:9px;font-size:13.5px;padding:6px 8px;border-radius:9px;transition:background .12s}
.rrow:hover{background:var(--track)}
.rrow .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:500}
.rrow .tags{display:flex;align-items:center;gap:4px;flex:none}
.tg{display:inline-flex;align-items:center;justify-content:center;height:16px;font-size:10px;font-weight:800;line-height:1;border-radius:5px;padding:0 5px;font-variant-numeric:tabular-nums}
.tg.g{background:rgba(52,199,89,.16);color:#1f9d4d}
.tg.a{background:var(--blue-soft);color:var(--blue)}
.tg.og{background:rgba(255,59,48,.14);color:var(--red)}
.tg.sub{background:var(--track);color:var(--mut);font-size:8.5px;letter-spacing:.4px}
.tg.subon{background:rgba(52,199,89,.14);color:#1f9d4d;font-size:9px}
.tg.suboff{background:rgba(255,159,10,.16);color:#c0820f;font-size:9px}
.tg.cd{width:11px;height:14px;border-radius:2.5px;padding:0;box-shadow:0 1px 2px rgba(0,0,0,.18)}
.tg.cd.y{background:#f5c518}
.tg.cd.r{background:#e0322b}
.rrow .rbar{width:72px;height:6px;border-radius:4px;background:var(--track);overflow:hidden;flex:none}
.rrow .rbar i{display:block;height:100%;border-radius:4px}
.rrow .rv{font-weight:800;font-variant-numeric:tabular-nums;min-width:30px;text-align:right;font-size:14px}
.r-hi i{background:var(--green)}.r-hi .rv{color:var(--green)}
.r-mid i{background:var(--blue)}.r-mid .rv{color:var(--blue)}
.r-lo i{background:#aeaeb2}.r-lo .rv{color:var(--mut)}
.potm{display:inline-flex;align-items:center;gap:6px;background:var(--tri);color:#fff;border-radius:999px;padding:3px 11px;font-size:11px;font-weight:700}
.potmbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;background:linear-gradient(90deg,rgba(255,159,10,.14),rgba(255,159,10,.03));border:1px solid rgba(255,159,10,.3);border-radius:12px;padding:10px 12px;margin-bottom:12px;font-size:13px}
.potmbar b{font-size:14px}
.potmbar .pm{color:var(--mut);font-size:12px}
.potmbar .why{color:var(--mut);font-style:italic;font-size:12px}
.rrow{cursor:pointer}
.rrow .rcar{color:var(--mut);font-weight:700;transition:transform .15s;flex:none}
.rrow.ropen .rcar{transform:rotate(90deg)}
.rdet{display:none;flex-wrap:wrap;gap:5px;padding:4px 0 10px 30px;margin-top:-2px}
.rdet.open{display:flex}
.bdchip{font-size:10.5px;border-radius:6px;padding:2px 7px;font-variant-numeric:tabular-nums;background:var(--track);color:var(--mut)}
.bdchip.pos{background:rgba(52,199,89,.14);color:#1f9d4d}
.bdchip.neg{background:rgba(255,69,58,.14);color:#d33}
.bdchip.base{background:var(--blue-soft);color:var(--blue);font-weight:600}
.bdchip.tot{background:var(--txt);color:var(--surface);font-weight:700}
.mvm{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.mvm .box{background:var(--bg);border-radius:10px;padding:10px 12px}
.mvm .box .k{font-size:11px;color:var(--mut)}
.mvm .box .v{font-size:15px;font-weight:700;margin-top:2px}
.mvm .ok{color:var(--green)}.mvm .no{color:var(--red)}
.locked{color:var(--mut);font-size:12px;text-align:center;padding:6px 0}
.locked b{color:var(--txt)}
.rteam{font-size:11px;font-weight:700;color:var(--mut);margin:8px 0 4px;display:flex;align-items:center;gap:6px}
.rrow .pos{font-size:9px;font-weight:800;letter-spacing:.3px;color:var(--mut);background:var(--track);border-radius:5px;padding:2px 0;width:34px;text-align:center;flex:none}
.rrow .pos-G{background:rgba(255,159,10,.16);color:#c77700}
.rrow .pos-D{background:rgba(48,140,217,.14);color:#2b6fbf}
.rrow .pos-M{background:rgba(52,199,89,.15);color:#1f9d4d}
.rrow .pos-F{background:rgba(255,59,48,.13);color:#d33}
.potm.sm{padding:1px 6px;font-size:10px;margin-left:6px;vertical-align:middle}
.cards,.subsl{display:flex;flex-direction:column;gap:6px;font-size:13.5px}
.cardr,.subr{display:flex;align-items:center;gap:9px}
.cardr .mn,.subr .mn{font-variant-numeric:tabular-nums;font-weight:700;min-width:34px}
.cardchip{width:11px;height:15px;border-radius:2px;display:inline-block}
.cardchip.y{background:#ffcc00}.cardchip.r{background:var(--red)}
.subr .in{color:var(--green);font-weight:600}.subr .out{color:var(--red)}
.subr .ar{color:var(--mut)}
.pitch{display:flex;flex-direction:column;gap:10px;background:linear-gradient(180deg,rgba(52,199,89,.10),rgba(52,199,89,.03));border-radius:12px;padding:14px 10px;margin-top:8px}
.pline{display:flex;justify-content:space-around;gap:6px;align-items:flex-start}
.pchip{display:flex;flex-direction:column;align-items:center;gap:3px;max-width:86px;min-width:48px}
.phead{width:38px;height:38px;border-radius:50%;background:var(--surface) center/cover no-repeat;display:flex;align-items:center;justify-content:center;box-shadow:var(--shadow);border:2px solid rgba(255,255,255,.14)}
.phead .pnum{font-weight:800;font-size:13px;color:var(--mut)}
.phead.has-img .pnum{display:none}
.pnm{font-size:10px;line-height:1.15;max-width:86px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:center;color:var(--txt)}
.pclub{display:block;font-size:8.5px;line-height:1.1;max-width:86px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:center;color:var(--mut);opacity:0;transition:opacity .2s}
.pclub.has-club{opacity:.85}
.pclub-i{font-size:10px;color:var(--mut);margin-left:6px;opacity:0}
.pclub-i.has-club{opacity:.8}
.luhdr{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--mut);margin-bottom:2px}
.luhdr b{color:var(--txt);font-size:13px}
.formtag{font-weight:800;color:var(--blue);font-variant-numeric:tabular-nums}
.tstat{display:flex;flex-direction:column;gap:13px;margin-top:10px}
.tsrow{display:grid;grid-template-columns:auto 1fr auto;grid-template-areas:"hv lbl av" "bar bar bar";gap:4px 10px;align-items:center}
.tsrow .tslbl{grid-area:lbl;text-align:center;font-size:10px;color:var(--mut);text-transform:uppercase;letter-spacing:.5px;font-weight:700}
.tsrow .tsv{font-weight:600;font-variant-numeric:tabular-nums;font-size:14px;color:var(--mut)}
.tsrow .tsv.h{grid-area:hv;text-align:left}
.tsrow .tsv.a{grid-area:av;text-align:right}
.tsrow .tsv.lead{color:var(--txt);font-weight:800}
.tsbar{grid-area:bar;display:flex;gap:3px;height:8px}
.tsbar i{display:block;height:100%;border-radius:4px;min-width:3px;transition:width .4s ease}
.tsbar i.h{background:var(--blue)}
.tsbar i.a{background:var(--amber)}
.tsbar i.lo{opacity:.3}
.pstat{width:100%;border-collapse:collapse;font-size:12px;margin-top:10px}
.pstat th,.pstat td{padding:6px 4px;text-align:center;font-variant-numeric:tabular-nums}
.pstat th{color:var(--mut);font-weight:800;font-size:9.5px;letter-spacing:.3px;border-bottom:1.5px solid var(--hair)}
.pstat td{border-bottom:1px solid var(--hair)}
.pstat tbody tr:last-child td{border-bottom:none}
.pstat tbody tr:hover td{background:var(--track)}
.pstat .pn{text-align:left;white-space:nowrap;max-width:150px;overflow:hidden;text-overflow:ellipsis;font-weight:500;color:var(--txt)}
.pstat th.pn{color:var(--txt);font-size:11.5px;font-weight:800;letter-spacing:.2px}
.pstat .z{color:var(--hair)}
.pstat td.hi{color:var(--blue);font-weight:800}
.tpiov{display:flex;justify-content:space-between;align-items:center;margin:6px 0 14px;gap:10px}
.tpiov .tpi{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--mut)}
.tpiov .tpi b{font-size:26px;font-weight:800;font-variant-numeric:tabular-nums;color:var(--txt);line-height:1}
.tpiov .tpi.h b{color:var(--blue)} .tpiov .tpi.a b{color:var(--amber)}
.sleaders{display:grid;grid-template-columns:repeat(auto-fit,minmax(146px,1fr));gap:8px;margin-top:10px}
.slchip{display:flex;flex-direction:column;gap:3px;background:var(--bg);border:1px solid var(--hair);border-radius:12px;padding:9px 12px}
.slchip .slk{font-size:9.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.4px;font-weight:700;display:flex;align-items:center;gap:5px}
.slchip .slv{font-size:13px;font-weight:500;display:flex;align-items:baseline;gap:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.slchip .slv b{font-size:18px;font-variant-numeric:tabular-nums;color:var(--blue);font-weight:800}
.slchip .slt{color:var(--mut);font-size:11px}
footer{margin-top:80px;padding:26px 22px 0;border-top:1px solid var(--hair);color:var(--mut);font-size:12px;text-align:center;line-height:1.8}
@media(max-width:640px){.hero h1{font-size:32px}}
.mv{font-weight:800;font-size:12px;font-variant-numeric:tabular-nums}
.mv.up{color:#1f9d4d}.mv.dn{color:var(--red)}.mv.fl{color:var(--mut)}
.elobar{display:inline-block;width:46px;height:5px;border-radius:3px;background:var(--track);vertical-align:middle;margin-right:6px;overflow:hidden}
.elobar i{display:block;height:100%;background:linear-gradient(90deg,var(--blue),#5aa6ff)}
.scen{margin-top:11px;border-top:1px solid var(--hair);padding-top:9px}
.scenh{font-size:10px;color:var(--mut);font-weight:800;text-transform:uppercase;letter-spacing:.5px;margin-bottom:7px}
.scenrow{display:flex;align-items:center;gap:7px;padding:3px 0;font-size:12.5px}
.scenrow .snm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600}
.stag{font-size:9.5px;font-weight:800;border-radius:5px;padding:2px 6px;white-space:nowrap}
.stag.thru{background:rgba(52,199,89,.16);color:#1f9d4d}
.stag.out{background:rgba(142,142,147,.18);color:var(--mut)}
.stag.hunt{background:var(--blue-soft);color:var(--blue)}
.sc3{font-size:10px;color:var(--mut);white-space:nowrap;font-variant-numeric:tabular-nums}
.sc3 b{color:var(--txt)}
.commlist{display:flex;flex-direction:column;max-height:360px;overflow-y:auto;margin-top:6px;padding-right:4px}
.commrow{display:flex;gap:9px;align-items:flex-start;padding:6px 4px;border-bottom:1px solid var(--hair);font-size:12.5px;line-height:1.42}
.commrow.big{background:rgba(52,199,89,.07);border-radius:7px;font-weight:600;border-bottom:none;margin:2px 0}
.commrow .cmn{flex:none;width:36px;color:var(--mut);font-weight:800;font-variant-numeric:tabular-nums;text-align:right}
.commrow .cic{flex:none;width:16px;text-align:center}
.commrow .ctx{flex:1;color:var(--txt)}
#tickerbar{display:none;gap:16px;overflow-x:auto;white-space:nowrap;padding:9px 14px;margin:0 0 14px;background:var(--surface);border:1px solid var(--hair);border-radius:12px;font-size:13px;align-items:center;box-shadow:var(--shadow)}
#tickerbar.show{display:flex}
#tickerbar::-webkit-scrollbar{height:0}
.tklbl{color:var(--live);font-weight:800;font-size:11px;letter-spacing:.5px;flex:none}
.tk{flex:none;color:var(--txt)}.tk b{font-variant-numeric:tabular-nums;color:var(--txt)}.tk.clk{cursor:pointer}
.tk .tkm{color:var(--live);font-weight:800;font-size:11px;margin-right:5px}
#goalflash{position:fixed;top:18px;left:50%;transform:translateX(-50%) translateY(-34px);opacity:0;pointer-events:none;z-index:200;transition:opacity .35s,transform .35s cubic-bezier(.2,.8,.2,1)}
#goalflash.show{opacity:1;transform:translateX(-50%) translateY(0)}
.gf-in{display:flex;align-items:center;gap:13px;background:linear-gradient(135deg,#1f9d4d,#34c759);color:#fff;padding:12px 22px;border-radius:14px;box-shadow:0 12px 44px rgba(0,0,0,.45)}
.gf-ball{font-size:26px}.gf-t{font-weight:900;font-size:15px;letter-spacing:.3px}.gf-s{font-size:12px;opacity:.93}
.callt{font-size:9px;font-weight:800;border-radius:5px;padding:2px 6px;margin-left:6px;background:var(--track);color:var(--mut);white-space:nowrap}
.callt.ok{background:rgba(52,199,89,.16);color:#1f9d4d}
.callt.mkt{background:rgba(255,159,10,.16);color:#c0820f}
.resrow{background:rgba(255,255,255,.04);border-radius:8px}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;scroll-behavior:auto!important}#goalflash{transition:none!important}}
</style>
</head>
<body>
<div id="goalflash"></div>
<nav><div class="in"><b><span class="lg">26</span> World Cup 26</b>
<a href="index.html">Forecast</a><a href="#feed" class="on">Live</a><a href="#stats">Stats</a><a href="#bestxi">Best XI</a><a href="#groups">Groups</a><a href="#odds">Title odds</a><a href="#power">Power</a><a href="#scorecard">Accuracy</a><a href="#bracket">Bracket</a><a href="#whatif">What if?</a></div></nav>
<div class="wrap">
<div id="tickerbar"></div>

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

<section id="stats">
 <div class="shead"><h2>Tournament stats</h2><p>Live leaderboards and model-driven storylines, built from real match data — the Golden Boot race, our own player power rankings, and how the tournament is defying (or matching) the forecast.</p></div>
 <div id="statsbox"></div>
</section>

<section id="bestxi">
 <div class="shead"><h2>Team of the Tournament</h2><p>The best XI so far by our player-rating model — highest average rating in each position, in a 4-3-3. Tap a player for their match-by-match form.</p></div>
 <div class="card" id="bestxibox" style="padding:18px"></div>
</section>

<section id="tracker">
 <div class="shead"><h2>Title race</h2><p>How each contender's championship probability has moved since kickoff — recomputed by the model after every result.</p></div>
 <div class="card" id="trackerbox" style="padding:18px"></div>
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

<section id="power">
 <div class="shead"><h2>Power Rankings</h2><p>All 48 teams by the model's team strength (Elo), with their live championship odds and how those have moved (Δ) since the pre-tournament forecast.</p></div>
 <div class="card tscroll" id="powerbox"></div>
</section>

<section id="scorecard">
 <div class="shead"><h2>Model accuracy — and how it's beating the market</h2><p>Every settled match scored against the model's pre-match prediction, using the same metrics serious forecasters report (Rank Probability Score, log loss, hit rate), benchmarked head-to-head against the betting market and a coin flip.</p></div>
 <div id="scorecardbox"></div>
</section>

<section id="bracket">
 <div class="shead"><h2>Projected bracket</h2><p>The current most-likely path given results so far — favourites advancing each tie, with live win probabilities. Completed knockout matches lock in automatically.</p></div>
 <div class="bwrap"><div class="bracket" id="btree"></div></div>
 <div class="note" id="bracketnote"></div>
</section>

<section id="whatif">
 <div class="shead"><h2>What-if simulator</h2><p>Set the result of any remaining group match and watch the model re-run thousands of tournaments live — see exactly how each scenario reshapes the title race. Stack as many as you like.</p></div>
 <div class="card" id="whatifbox" style="padding:16px"></div>
</section>

<footer>
 Live engine runs entirely in your browser: <span id="ftN"></span> Monte-Carlo tournaments per refresh, conditioned on real results fetched from the open match database.<br>
 Pre-tournament model: penalised Dixon-Coles (ξ=0.4/yr) ⊗ World Football Elo · Bracket &amp; Annex C: FIFA regulations.<br>
 Unofficial fan analytics project — not affiliated with or endorsed by FIFA. Remaining-match probabilities use the pre-tournament model; played results are locked in.
</footer>
</div>

<div class="ov" id="wpov"><div class="modal" id="wpmodal"></div></div>
<div class="ov" id="tmov"><div class="modal" id="tmmodal"></div></div>

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

/* ---- formation layout: vertical tier (0=GK..5=FWD) + horizontal side (-2 wide L .. +2 wide R) from ESPN position abbreviation ---- */
function posTier(ab){ const a=String(ab||"").toUpperCase().replace(/[^A-Z]/g,"");
 if(a==="G"||a==="GK") return 0;
 if(/ST|CF|SS|^F$|RF|LF|RW|LW/.test(a)) return 5;
 if(/AM/.test(a)) return 4;
 if(/DM/.test(a)) return 2;
 if(/M/.test(a)) return 3;
 if(/CB|RB|LB|WB|SW|D/.test(a)||/B$/.test(a)) return 1;
 return 3; }
function posSide(ab){ const a=String(ab||"").toUpperCase();
 if(/-R$/.test(a)) return 1; if(/-L$/.test(a)) return -1;
 if(/^R/.test(a)) return 2; if(/^L/.test(a)) return -2; return 0; }
function escAttr(s){ return String(s||"").replace(/&/g,"&amp;").replace(/"/g,"&quot;"); }

/* ---- player headshots from Wikipedia (CORS-open REST summary); cached in memory + localStorage; footballer-verified ---- */
const PHOTOS={}, PHOTO_REQ={};
function photoGet(n){ if(n in PHOTOS) return PHOTOS[n]; try{const v=localStorage.getItem("wcph2:"+n); if(v) return (PHOTOS[n]=v);}catch(e){} return undefined; }
function photoSetPos(n,url){ PHOTOS[n]=url; try{localStorage.setItem("wcph2:"+n,url);}catch(e){} }   // positive: persist
function photoSetNeg(n){ if(!(n in PHOTOS)) PHOTOS[n]=""; }                                            // genuine miss: memory only (retry next session)
const FB_RE=/foot(ball)?|soccer|winger|midfield|defender|goalkeep|striker|forward/;   // footballer description guard (avoid same-name people)
const psleep=ms=>new Promise(r=>setTimeout(r,ms));
// throttle concurrent lookups so a full lineup doesn't burst the APIs into HTTP 429
let PHOTO_ACTIVE=0; const PHOTO_Q=[];
function photoSchedule(fn){ return new Promise(res=>{ PHOTO_Q.push({fn,res}); photoPump(); }); }
function photoPump(){ while(PHOTO_ACTIVE<3 && PHOTO_Q.length){ const job=PHOTO_Q.shift(); PHOTO_ACTIVE++;
  Promise.resolve().then(job.fn).then(v=>{PHOTO_ACTIVE--;job.res(v);photoPump();},()=>{PHOTO_ACTIVE--;job.res(null);photoPump();}); } }
// fetch with retry on 429/5xx; returns null on persistent transient failure (so it is NOT cached and retries later)
async function pfetch(url){ for(let i=0;i<3;i++){ try{ const r=await fetch(url); if(r.status===429||r.status>=500){ await psleep(700*(i+1)+Math.random()*500); continue; } return r; }catch(e){ await psleep(500*(i+1)); } } return null; }
// each tier returns: URL (found) | "" (genuine 200 with no image) | null (transient — don't cache)
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
// combined chain: Wikipedia -> Wikidata; throttled; caches only definite results; transient failures retry on next render
function fetchPlayerPhoto(name){
 const cached=photoGet(name); if(cached!==undefined) return Promise.resolve(cached);
 if(PHOTO_REQ[name]) return PHOTO_REQ[name];
 const p=(async()=>{
   const w=await photoSchedule(()=>wikiSummaryPhoto(name)); if(w){ photoSetPos(name,w); return w; }
   const d=await photoSchedule(()=>wikidataPhoto(name)); if(d){ photoSetPos(name,d); return d; }
   if(w!==null && d!==null) photoSetNeg(name);   // both tiers definitively had no image
   return "";
 })();
 PHOTO_REQ[name]=p;
 p.then(()=>{ if(photoGet(name)===undefined) delete PHOTO_REQ[name]; });   // transient (uncached) → allow a later retry
 return p;
}
function applyPhoto(el,url){ if(!url||!el)return; const img=new Image();
 img.onload=()=>{ el.style.backgroundImage="url('"+url.replace(/'/g,"%27")+"')"; el.classList.add("has-img"); }; img.src=url; }
function hydratePhotos(root){ (root||document).querySelectorAll(".phead[data-pl]").forEach(el=>{
 const nm=el.getAttribute("data-pl"); if(!nm)return;
 fetchPlayerPhoto(nm).then(url=>{ if(url) applyPhoto(el,url); }); }); }

/* ---- player's current club via ESPN athlete endpoint (CORS-open), keyed by ESPN athlete id; cached in memory + localStorage ---- */
const CLUBS={}, CLUB_REQ={}, CLUBLG={};
function clubGet(id){ if(id in CLUBS) return CLUBS[id]; try{const v=localStorage.getItem("wccl1:"+id); if(v!=null) return (CLUBS[id]=v);}catch(e){} return undefined; }
function clubSet(id,nm){ CLUBS[id]=nm; try{localStorage.setItem("wccl1:"+id,nm);}catch(e){} }
function lgGet(id){ if(id in CLUBLG) return CLUBLG[id]; try{const v=localStorage.getItem("wclg1:"+id); if(v!=null) return (CLUBLG[id]=v);}catch(e){} return undefined; }
// league-pedigree weight by league code (slug prefix) — top-5 European > other strong leagues > mid > rest
function lgTier(code){ code=(code||"").toLowerCase();
  if(["eng","esp","ger","ita","fra"].includes(code)) return 1.0;
  if(["por","ned","tur","bel","sco","aut","sui","gre","ukr","rus","den","cro","srb","cze"].includes(code)) return 0.72;
  if(["usa","mex","bra","arg","sau","jpn","kor","qat","uae","col","gre","nor","swe","pol"].includes(code)) return 0.55;
  return 0.4; }
// returns club name (found) | "" (player has no club / 404) | null (transient — don't cache, retry next render)
async function espnAthleteClub(id){
  const r=await pfetch("https://site.web.api.espn.com/apis/common/v3/sports/soccer/all/athletes/"+encodeURIComponent(id));
  if(!r) return null; if(r.status===404) return ""; if(!r.ok) return null;
  try{ const d=await r.json(); const a=d.athlete||d; const t=a.team||{};
    const lg=String(t.slug||"").split(".")[0]; if(id&&lg){ CLUBLG[id]=lg; try{localStorage.setItem("wclg1:"+id,lg);}catch(e){} }
    return t.shortDisplayName||t.displayName||t.name||""; }catch(e){ return null; }
}
function fetchClub(id){
  if(!id) return Promise.resolve("");
  const c=clubGet(id); if(c!==undefined) return Promise.resolve(c);
  if(CLUB_REQ[id]) return CLUB_REQ[id];
  const p=(async()=>{ const v=await photoSchedule(()=>espnAthleteClub(id));   // share the photo throttle so a lineup doesn't burst ESPN
    if(v){ clubSet(id,v); return v; } if(v===""){ clubSet(id,""); } return ""; })();
  CLUB_REQ[id]=p;
  p.then(()=>{ if(clubGet(id)===undefined) delete CLUB_REQ[id]; });   // transient (uncached) → allow a later retry
  return p;
}
function hydrateClubs(root){ (root||document).querySelectorAll("[data-club]").forEach(el=>{
 const id=el.getAttribute("data-club"); if(!id)return;
 fetchClub(id).then(nm=>{ if(nm){ el.textContent=nm; el.classList.add("has-club"); } }); }); }
// Squad pedigree: average league tier of the named XI (on-paper club quality). DISPLAY ONLY —
// it does NOT feed the forecast (which stays results-based and out-of-sample validated).
function teamPedi(b){ if(!b||!b.xi)return null; let s=0,n=0;
 b.xi.forEach(p=>{ if(p.aid!=null){ const lg=lgGet(p.aid); if(lg){ s+=lgTier(lg); n++; } } });
 return n>=6 ? {idx:Math.round(100*s/n), n} : null; }
function hydratePedigree(root, lu){
 const el=(root||document).querySelector("#pedibar"); if(!el||!lu)return;
 Promise.all(["home","away"].map(side=>{ const b=lu[side]; if(!b||!b.xi)return Promise.resolve(null);
   return Promise.all(b.xi.filter(p=>p.aid).map(p=>fetchClub(p.aid))).then(()=>teamPedi(b)); }))
  .then(([h,a])=>{ if(!h&&!a)return; const f=fixById[WP.fid]; if(!f)return;
    const hi=h?h.idx:0, ai=a?a.idx:0, mx=Math.max(hi,ai,1);
    const seg=(v,nm,n)=>`<div class="pedrow"><span class="pednm">${nm}</span><span class="pedbar"><i style="width:${(100*v/mx).toFixed(0)}%"></i></span><span class="pedv">${v}${n?` <span class="pedn">${n}/11</span>`:""}</span></div>`;
    el.innerHTML=`<div class="mcsec"><h4>Squad pedigree <span class="tag">on-paper club quality · not a forecast input</span></h4>`+
      (h?seg(h.idx,F(f.home)+" "+f.home,h.n):"")+(a?seg(a.idx,F(f.away)+" "+f.away,a.n):"")+
      `<div class="heatcap">Average league strength of the starting XI (share at top-5 European &amp; other strong leagues), from each player's current club. Indicative only — the win-probability model is driven by team results, not this.</div></div>`;
  }); }

let STATE={results:{},ko:{},live:{},source:"snapshot",fetchedUTC:null,played:0};

/* ---- martj42 CSV feed (fallback source; finals only) ---- */
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
 const results={};
 rows.forEach(r=>{
  if(r.hs===""||r.hs==null||isNaN(+r.hs)) return;
  const id=fixByPair[r.home+"|"+r.away];
  if(id!=null){ results[id]=[+r.hs,+r.as]; }
 });
 return results;
}
async function loadMartj42(){
 const res=await fetch(FEED,{cache:"no-store"});
 if(!res.ok) throw new Error("martj42 HTTP "+res.status);
 return ingest(parseCSV(await res.text()));   // {fid:[h,a]} finals
}

/* ---- ESPN live source: fresh scores + goal minutes, CORS-open (site.api.espn.com) ----
   Authoritative, real-time. Finals feed the Monte Carlo; live matches drive the in-play
   chart at the true scoreline; goal details (minute/side/pen/og) match our goal_events
   convention (team = side the goal counts for). Best-effort; falls back to martj42/snapshot. */
const ESPN_SB="https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard";
const ESPN_SUM="https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary";
const ESPN_ALIAS={"bosnia herzegovina":"Bosnia and Herzegovina","congo dr":"DR Congo","czechia":"Czech Republic","turkiye":"Turkey","usa":"United States","korea republic":"South Korea","ir iran":"Iran","cote divoire":"Ivory Coast","cabo verde":"Cape Verde"};
function espnNorm(s){ s=(s||"").normalize("NFKD").replace(/[\u0300-\u036f]/g,"").toLowerCase(); for(const ch of ".-&/'") s=s.split(ch).join(" "); return s.replace(/\s+/g," ").trim(); }
const CANON_BY_NORM=(()=>{const m={};D.fixtures.forEach(f=>{m[espnNorm(f.home)]=f.home;m[espnNorm(f.away)]=f.away;});return m;})();
function espnCanon(name){ const n=espnNorm(name); if(CANON_BY_NORM[n])return CANON_BY_NORM[n]; if(ESPN_ALIAS[n])return ESPN_ALIAS[n];
 for(const k in CANON_BY_NORM){ if(n.length>=4&&(k.includes(n)||n.includes(k)))return CANON_BY_NORM[k]; } return null; }
function espnMinute(e){ const dc=(e.status&&(e.status.displayClock||(e.status.type&&e.status.type.shortDetail)))||"";
 const m=String(dc).match(/(\d+)/); return m?Math.max(0,Math.min(90,parseInt(m[1],10))):null; }
function espnAdded(e){ const dc=(e.status&&e.status.displayClock)||""; const m=String(dc).match(/\+\s*(\d+)/); return m?parseInt(m[1],10):0; }   // stoppage minutes from "90'+4'"
function espnDateRange(){   // YYYYMMDD-YYYYMMDD spanning the tournament so far (+ today's late games)
 const ds=D.fixtures.filter(f=>f.utc).map(f=>new Date(f.utc).getTime()); if(!ds.length) return null;
 const fmt=ms=>new Date(ms).toISOString().slice(0,10).replace(/-/g,"");
 return fmt(Math.min(...ds))+"-"+fmt(Math.min(Date.now()+6*3600e3, Math.max(...ds)));
}
function parseESPN(d){
 const finals={}, live={}, goals={}, post=[], kick={};
 (d.events||[]).forEach(e=>{
  const comp=e.competitions&&e.competitions[0]; if(!comp) return;
  const cs=comp.competitors||[];
  const hc=cs.find(c=>c.homeAway==="home"), ac=cs.find(c=>c.homeAway==="away"); if(!hc||!ac) return;
  const home=espnCanon(hc.team&&hc.team.displayName), away=espnCanon(ac.team&&ac.team.displayName); if(!home||!away) return;
  const fid=fixByPair[home+"|"+away]; if(fid==null) return;   // unknown/reversed pairing → leave to martj42
  if(e.date) kick[fid]=e.date;                                 // ESPN's authoritative kickoff time (UTC)
  const state=(e.status&&e.status.type&&e.status.type.state)||"pre";   // pre | in | post
  const hs=+hc.score, as=+ac.score, key=home+"|"+away;
  const idSide={}; cs.forEach(c=>{ if(c.team) idSide[c.team.id]=c.homeAway; });
  const ev=[];
  (comp.details||[]).forEach(x=>{ if(!x.scoringPlay) return;
   const side=idSide[x.team&&x.team.id]; if(!side) return;
   const dv=String((x.clock&&x.clock.displayValue)||""); const bm=dv.match(/\d+/), pm=dv.match(/\+\s*(\d+)/);   // "90'+4'" -> base 90, add 4
   const o={min:bm?Math.min(90,parseInt(bm[0],10)):0, team:side}; if(pm)o.add=parseInt(pm[1],10);
   if(x.ownGoal)o.og=true; if(x.penaltyKick)o.pen=true; ev.push(o);
  });
  ev.sort((a,b)=>a.min-b.min);
  if(state==="post"){ finals[fid]=[hs,as]; if(ev.length)goals[key]=ev; post.push({key,eid:e.id}); }
  else if(state==="in"){ live[fid]={hs,as,minute:espnMinute(e),added:espnAdded(e),eid:e.id,key}; goals[key]=ev; }
 });
 return {finals,live,goals,post,kick};
}
// ESPN per-player stat name -> our short column (mirrors fetch_espn.PLAYER_STATS)
const ESPN_PSTAT={totalGoals:"G",goalAssists:"A",totalShots:"SH",shotsOnTarget:"SOT",foulsCommitted:"FC",foulsSuffered:"FS",offsides:"OFF",yellowCards:"YC",redCards:"RC",saves:"SV",goalsConceded:"GC",shotsFaced:"SF"};
// ESPN team stat name -> [label, isPercent], in display order (mirrors fetch_espn.TEAM_STATS)
const ESPN_TSTAT=[["possessionPct","Possession",true],["totalShots","Shots",false],["shotsOnTarget","Shots on Target",false],["wonCorners","Corners",false],["totalPasses","Passes",false],["foulsCommitted","Fouls",false],["offsides","Offsides",false],["yellowCards","Yellow Cards",false],["redCards","Red Cards",false],["totalTackles","Tackles",false],["interceptions","Interceptions",false],["saves","Saves",false]];
function espnPosBucket(name){ const n=String(name||"").toLowerCase();
 if(n.includes("keeper")||n.includes("goal"))return"G";
 if(n.includes("defend")||n.includes("back")||n.includes("sweeper"))return"D";
 if(n.includes("midfield"))return"M";
 if(["forward","striker","wing","attack"].some(w=>n.includes(w)))return"F";
 return"M"; }
function espnPlayerStats(p){ const raw={}; (p.stats||[]).forEach(s=>{ if(s&&s.name!=null)raw[s.name]=s.displayValue; });
 const out={}; for(const en in ESPN_PSTAT){ const v=raw[en]; if(v==null||v==="")continue; const n=parseFloat(v); out[ESPN_PSTAT[en]]=isNaN(n)?v:Math.round(n); }
 return Object.keys(out).length?out:null; }
function espnEvMin(ev){ const c=(ev.clock&&ev.clock.displayValue)||ev.time||""; const m=String(c).match(/(\d+)/); return m?parseInt(m[1],10):0; }
// Build the data/lineups.json record (formation/XI/subs/per-player stats/cards/subs/teamstats) from an ESPN
// summary. Teams are oriented to OUR canonical home/away BY NAME, so it's robust to ESPN's home/away choice.
function buildLineupFromSummary(s, home, away){
 const rosters=s.rosters||[]; if(!rosters.length) return null;
 const sideOf=tn=>{const c=espnCanon(tn); return c===home?"home":c===away?"away":null;};
 const blocks={};
 rosters.forEach(r=>{ const side=sideOf((r.team&&r.team.displayName)||""); if(!side) return;
  const xi=[], subs=[];
  (r.roster||[]).forEach(p=>{ const ath=p.athlete&&p.athlete.displayName; if(!ath) return;
   const pos=p.position||{}; const e={name:ath,num:p.jersey,pos:espnPosBucket(pos.displayName||pos.name||pos.abbreviation),posAbbr:(pos.abbreviation||""),fp:p.formationPlace,aid:(p.athlete&&p.athlete.id)||null};
   const st=espnPlayerStats(p); if(st)e.st=st;
   (p.starter?xi:subs).push(e); });
  blocks[side]={formation:r.formation||"",xi:xi.slice(0,11),subs}; });
 if(!("home" in blocks)&&!("away" in blocks)) return null;
 const events=[];   // goals / cards / subs from keyEvents
 (s.keyEvents||s.commentary||[]).forEach(ev=>{ const t=ev.type||{}; const tt=String(t.type||t.text||"").toLowerCase();
  const side=sideOf((ev.team&&ev.team.displayName)||""); if(!side) return;
  const who=(ev.participants||[]).map(p=>p.athlete&&p.athlete.displayName).filter(Boolean); const mn=espnEvMin(ev);
  const isGoal = ev.scoringPlay===true || (tt.includes("goal")&&!tt.includes("no goal"));   // "penalty---scored" has no "goal" in its type, so trust scoringPlay
  if(/own.?goal/.test(tt)) events.push({min:mn,team:side,type:"goal",detail:"Own Goal",player:who[0]||null});   // ESPN type is "own-goal" (hyphen) — match space/hyphen/joined
  else if(isGoal) events.push(Object.assign({min:mn,team:side,type:"goal",detail:tt.includes("penalt")?"Penalty":"Normal Goal",player:who[0]||null}, who.length>1?{assist:who[1]}:{}));
  else if(tt.includes("yellow")) events.push({min:mn,team:side,type:"card",card:"yellow",player:who[0]||null});
  else if(tt.includes("red")) events.push({min:mn,team:side,type:"card",card:"red",player:who[0]||null});
  else if(tt.includes("substitut")) events.push({min:mn,team:side,type:"subst",assist:who[0]||null,player:who.length>1?who[1]:null});
 });
 // reconcile cards against per-player boxscore YC/RC (drop overturned VAR cards; never invent one)
 const tally={};
 rosters.forEach(r=>(r.roster||[]).forEach(p=>{ const nm=p.athlete&&p.athlete.displayName; if(!nm)return;
  const raw={}; (p.stats||[]).forEach(s2=>{if(s2&&s2.name!=null)raw[s2.name]=s2.displayValue;});
  if(Object.keys(raw).length){ const gi=k=>{const n=parseFloat(raw[k]);return isNaN(n)?0:Math.round(n);}; tally[espnNorm(nm)]={yellow:gi("yellowCards"),red:gi("redCards")}; } }));
 const evs=events.filter(e=>{ if(e.type!=="card")return true; const ta=tally[espnNorm(e.player||"")]; if(!ta)return true; return (ta[e.card]||0)>0; });
 // team match stats from the boxscore
 const ts={home:{},away:{},labels:{},pct:{}};
 ((s.boxscore&&s.boxscore.teams)||[]).forEach(t=>{ const side=sideOf((t.team&&t.team.displayName)||""); if(!side)return;
  const have={}; (t.statistics||[]).forEach(st=>{if(st&&st.name)have[st.name]=st;});
  ESPN_TSTAT.forEach(function(row){ const name=row[0]; const st=have[name];
   if(!st||st.displayValue==null||st.displayValue==="")return; ts[side][name]=st.displayValue; ts.labels[name]=row[1]; ts.pct[name]=row[2]; }); });
 const rec={status:"LIVE",source:"espn",home:blocks.home||{formation:"",xi:[],subs:[]},away:blocks.away||{formation:"",xi:[],subs:[]},events:evs};
 if(Object.keys(ts.home).length||Object.keys(ts.away).length) rec.teamstats=ts;
 return rec;
}
// Fetch one summary and use it to (a) attach scorer names to the goal timeline and (b) build the live Match Centre record.
function mlToProb(ml){ ml=+ml; if(isNaN(ml))return null; return ml>0 ? 100/(ml+100) : (-ml)/((-ml)+100); }
function parseMarket(s){   // betting-market implied H/D/A probabilities (over-round removed)
 const pc=(s.pickcenter||[]).find(o=>o&&o.homeTeamOdds&&o.awayTeamOdds&&o.homeTeamOdds.moneyLine!=null&&o.awayTeamOdds.moneyLine!=null);
 if(!pc)return null;
 const h=mlToProb(pc.homeTeamOdds.moneyLine), a=mlToProb(pc.awayTeamOdds.moneyLine), d=mlToProb(pc.drawOdds&&pc.drawOdds.moneyLine);
 if(h==null||a==null)return null; const dd=d==null?0:d; const tot=h+dd+a; if(tot<=0)return null;
 return {h:h/tot,d:dd/tot,a:a/tot,prov:(pc.provider&&pc.provider.name)||"Market"};
}
function commentaryType(t){ t=(t||"").toLowerCase();
 if(/own.?goal/.test(t)) return "og";
 if(/\bgoal\b|scores|back of the net/.test(t)) return "goal";
 if(/penalty/.test(t)) return "pen";
 if(/red card|sent off|second yellow/.test(t)) return "red";
 if(/yellow card|booked|is shown/.test(t)) return "yellow";
 if(/substitution|replaces/.test(t)) return "sub";
 if(/saved|save\b/.test(t)) return "save";
 if(/attempt missed|misses|off target|hits the (post|bar)|blocked/.test(t)) return "miss";
 if(/corner/.test(t)) return "corner";
 if(/offside/.test(t)) return "offside";
 if(/foul|free kick/.test(t)) return "foul";
 if(/half begins|half ends|kick.?off|full.?time|half.?time|delay/.test(t)) return "whistle";
 return ""; }
function parseCommentary(s){
 return (s.commentary||[]).map(c=>{ const tv=(c.time&&c.time.displayValue)||""; const m=String(tv).match(/(\d+)(?:'?\s*\+\s*(\d+))?/);
   return {min:m?parseInt(m[1],10):null, add:(m&&m[2])?parseInt(m[2],10):0, text:(c.text||"").trim(), type:commentaryType(c.text)}; })
  .filter(c=>c.text);
}
async function espnSummaryHydrate(key, eid, goals, lineups){
 try{
  const r=await fetch(ESPN_SUM+"?event="+eid,{cache:"no-store"}); if(!r.ok)return;
  const s=await r.json();
  if(goals && goals[key]){ const byMin={};
   (s.keyEvents||[]).forEach(x=>{ if(!x.scoringPlay)return;
    const bm=String((x.clock&&x.clock.displayValue)||"").match(/\d+/); const mn=bm?Math.min(90,parseInt(bm[0],10)):null;   // base minute, stoppage clamped to 90
    const nm=x.participants&&x.participants[0]&&x.participants[0].athlete&&x.participants[0].athlete.displayName;
    if(mn!=null&&nm&&byMin[mn]==null)byMin[mn]=nm; });
   goals[key].forEach(g=>{ if(byMin[g.min])g.name=byMin[g.min]; });
  }
  const i=key.indexOf("|"); const rec=buildLineupFromSummary(s, key.slice(0,i), key.slice(i+1));
  if(rec){ rec.commentary=parseCommentary(s); rec.market=parseMarket(s); lineups[key]=rec; }
 }catch(_){}
}
async function loadESPN(){
 const range=espnDateRange();
 const res=await fetch(ESPN_SB+(range?"?dates="+range:""),{cache:"no-store"});
 if(!res.ok) throw new Error("ESPN HTTP "+res.status);
 const parsed=parseESPN(await res.json());
 parsed.lineups={};
 const jobs=[];
 // live matches: refresh scorer names + the full Match Centre (lineups/stats/cards/subs) every cycle
 Object.values(parsed.live).forEach(lv=>jobs.push(espnSummaryHydrate(lv.key, lv.eid, parsed.goals, parsed.lineups)));
 // finished matches missing from embedded lineups, OR whose embedded lineup predates formation data: hydrate once
 const hasFP=lu=>lu&&["home","away"].some(t=>lu[t]&&(lu[t].xi||[]).some(p=>p.fp!=null));
 const goalsNamed=k=>{const g=D.goal_events[k]; return g&&g.length&&g.every(x=>x.og||x.name);};
 (parsed.post||[]).forEach(pm=>{ const ex=D.lineups&&D.lineups[pm.key]; if(!ex || !hasFP(ex) || !goalsNamed(pm.key)) jobs.push(espnSummaryHydrate(pm.key, pm.eid, parsed.goals, parsed.lineups)); });
 await Promise.all(jobs);
 return parsed;
}

async function loadLive(){
 setStatus("loading");
 let espn=null, mart=null, err=null;
 try{ espn=await loadESPN(); }catch(e){ err=e; }
 try{ mart=await loadMartj42(); }catch(e){ if(!espn) err=e; }
 if(espn||mart){
  const results=Object.assign({}, mart||{}, espn?espn.finals:{});   // ESPN finals win ties
  const live=espn?espn.live:{};
  if(espn){
   for(const k in espn.goals){
    const isLive=Object.keys(live).some(fid=>live[fid].key===k);
    const newNm=espn.goals[k].some(g=>g.name), oldNm=D.goal_events[k]&&D.goal_events[k].some(g=>g.name);
    if(isLive || !D.goal_events[k] || !D.goal_events[k].length || (newNm && !oldNm)) D.goal_events[k]=espn.goals[k]; // fresh for live; fill gaps; upgrade nameless→named; keep richer embedded finals
   }
   if(!D.lineups) D.lineups={};
   for(const k in espn.lineups){ D.lineups[k]=espn.lineups[k]; }   // live = fresh each cycle; just-finished = fill once
   if(espn.kick){ D.fixtures.forEach(f=>{ if(espn.kick[f.id]) f.utc=espn.kick[f.id]; }); }   // correct kickoff times from ESPN (authoritative)
  }
  STATE={results,ko:{},live,source:espn?"espn":"live",fetchedUTC:new Date(),
   played:Object.keys(results).length, liveCount:Object.keys(live).length, err:espn?null:String((err&&err.message)||err||"")};
 }else{
  const results={};   // last resort: embedded pre-built snapshot
  D.snapshot.forEach(s=>{const id=fixByPair[s.home+"|"+s.away]; if(id!=null)results[id]=[s.hs,s["as"]];});
  STATE={results,ko:{},live:{},source:"snapshot",fetchedUTC:new Date(),played:Object.keys(results).length,err:String((err&&err.message)||err)};
 }
 recompute();
}

/* ---- run the Monte Carlo + render ---- */
let LAST=null, STATAGG={ratingAcc:{},gkAcc:{}}, PREVSCORES=null;
function recompute(){
 setStatus("sim");
 setTimeout(()=>{                       // let the spinner paint
  const out=WCLive.runLive(D,{N:NSIMS,results:STATE.results,ko:STATE.ko});
  LAST=out;
  renderStatus(); renderBig(out); renderFeed(); renderStats(); renderBestXI(); renderTracker(); renderGroups(out); renderOdds(out); renderPower(out); renderModelScore(); renderBracket(out); renderWhatIf(); renderTickerBar(); refreshOpenModal(); detectGoals();
 },20);
}
/* ---- live score ticker + goal flash ---- */
function renderTickerBar(){
 const el=document.getElementById("tickerbar"); if(!el)return;
 const items=Object.keys(STATE.live||{}).map(fid=>{const lv=STATE.live[fid],f=fixById[fid]; if(!f)return"";
   return `<span class="tk clk" data-fid="${fid}"><span class="tkm">${lv.minute!=null?(lv.minute>=90&&lv.added?"90+"+lv.added:lv.minute)+"'":"LIVE"}</span>${F(f.home)} <b>${lv.hs}</b>–<b>${lv.as}</b> ${F(f.away)}</span>`;}).filter(Boolean).join("");
 if(items){ el.innerHTML=`<span class="tklbl">● LIVE NOW</span>${items}`; el.classList.add("show"); }
 else el.classList.remove("show");
}
function detectGoals(){
 const cur={};
 for(const fid in (STATE.live||{})){ const lv=STATE.live[fid]; cur[fid]=(+lv.hs||0)+(+lv.as||0); }
 for(const fid in (STATE.results||{})){ const r=STATE.results[fid]; cur[fid]=(+r[0]||0)+(+r[1]||0); }
 if(PREVSCORES){ for(const fid in cur){ if(cur[fid]>(PREVSCORES[fid]||0) && STATE.live && STATE.live[fid]){
   const lv=STATE.live[fid], f=fixById[fid]; if(!f)continue;
   const ev=D.goal_events[f.home+"|"+f.away]||[]; const last=ev[ev.length-1];
   const pt= last ? (last.og?(last.team==="home"?"away":"home"):last.team) : (lv.hs>lv.as?"home":"away");
   flashGoal(f, pt==="home"?f.home:f.away, (last&&last.name)||"", lv);
 } } }
 PREVSCORES=cur;
}
function flashGoal(f,team,scorer,lv){
 const el=document.getElementById("goalflash"); if(!el)return;
 el.innerHTML=`<div class="gf-in"><span class="gf-ball">⚽</span><div><div class="gf-t">GOAL · ${F(team)} ${team}</div><div class="gf-s">${scorer?scorer+" — ":""}${F(f.home)} ${lv.hs}–${lv.as} ${F(f.away)}</div></div></div>`;
 el.classList.add("show"); clearTimeout(el._t); el._t=setTimeout(()=>el.classList.remove("show"),6500);
}
/* keep an open in-play popup tracking a live match as new goals arrive */
function matchFull(){    // effective final minute for the chart/model — extends into stoppage while live
 let mx=90; (WP.events||[]).forEach(e=>{const m=e.min+(e.add||0); if(m>mx)mx=m;});
 if(WP.status==="live"){
   const lv=STATE.live&&STATE.live[WP.fid]; const added=(lv&&lv.added)||0; const m=(lv&&lv.minute)||0;
   return (m>=90 && added>0) ? Math.max(mx,90+added)+3 : 90;   // extend past 90 only in 2nd-half stoppage (90'+x), NOT first-half (45'+x)
 }
 return mx;   // finished: locks at the last goal (>=90)
}
function refreshOpenModal(){
 if(!ov.classList.contains("show") || WP.fid==null) return;
 if(matchStatus(WP.fid)!=="live" || animTimer || !WP.followLive) return;   // only follow live; never fight Replay or a manual scrub
 const f=fixById[WP.fid]; const known=D.goal_events[f.home+"|"+f.away];
 WP.events = known ? known.map(e=>({...e})) : [];
 WP.reds = redsOf(f);
 const lv=STATE.live&&STATE.live[WP.fid]; const added=(lv&&lv.added)||0;
 if(lv && lv.minute!=null){ const m=Math.max(0,Math.min(90,lv.minute)); WP.minute = (m>=90 && added>0) ? 90+added : m; }
 WP.full = matchFull();
 drawModal();
}

/* Title race — championship probability over time */
function renderTracker(){
 const box=document.getElementById("trackerbox");
 const H=D.odds_history||[];
 if(!H.length){ box.innerHTML=`<div class="locked">The title-race chart builds as the tournament progresses.</div>`; return; }
 const latest=H[H.length-1].champ;
 const teams=Object.entries(latest).sort((a,b)=>b[1]-a[1]).slice(0,6).map(x=>x[0]);
 const maxP=Math.max(0.05,...teams.map(t=>Math.max(...H.map(h=>h.champ[t]||0))));
 const PADL=46,PADR=150,PADT=16,PADB=30,W=1000,Hh=360;
 const x=i=>PADL+(H.length<=1?0.5:(i/(H.length-1)))*(W-PADL-PADR);
 const y=p=>PADT+(1-p/(maxP*1.12))*(Hh-PADT-PADB);
 const pal=["#1e6fd9","#d92d2d","#00854d","#bf5af2","#ff9f0a","#34c759"];
 const grid=[0,.25,.5,.75,1].map(fr=>{const p=fr*maxP*1.12;
   return `<line class="gridln" x1="${PADL}" y1="${y(p)}" x2="${W-PADR}" y2="${y(p)}"/><text class="axt" x="${PADL-6}" y="${y(p)+4}" text-anchor="end">${(p*100).toFixed(0)}%</text>`;}).join("");
 const xt=H.map((h,i)=>`<text class="axt" x="${x(i)}" y="${Hh-9}" text-anchor="middle">${h.date.slice(5)}</text>`).join("");
 const lines=teams.map((t,ti)=>{const c=pal[ti%pal.length];
   const pts=H.map((h,i)=>x(i)+","+y(h.champ[t]||0)).join(" ");
   const dots=H.map((h,i)=>`<circle cx="${x(i)}" cy="${y(h.champ[t]||0)}" r="3" fill="${c}"/>`).join("");
   const last=H[H.length-1].champ[t]||0;
   return `<polyline fill="none" stroke="${c}" stroke-width="2.5" points="${pts}"/>${dots}<text x="${W-PADR+10}" y="${y(last)+4}" class="axt" fill="${c}" font-weight="700">${F(t)} ${t} ${(last*100).toFixed(1)}%</text>`;
 }).join("");
 box.innerHTML=`<svg viewBox="0 0 ${W} ${Hh}" preserveAspectRatio="xMidYMid meet" style="width:100%;height:auto">${grid}${xt}${lines}</svg>`;
}

/* tournament stats — leaderboards + model storylines, from real data */
function scoreFromGE(ev){let h=0,a=0;ev.forEach(e=>{e.team==="home"?h++:a++;});return [h,a];}
function matchScore(f,ev){ if(f&&STATE.results&&STATE.results[f.fid])return STATE.results[f.fid];
 let h=0,a=0; ev.forEach(e=>{const pt=e.og?(e.team==="home"?"away":"home"):e.team; pt==="home"?h++:a++;}); return [h,a]; }
function renderStats(){
 const box=document.getElementById("statsbox");
 const fxKey={}; D.fixtures.forEach(f=>fxKey[f.home+"|"+f.away]=f);
 const keys=Object.keys(D.goal_events).filter(k=>fxKey[k]);
 if(!keys.length){ box.innerHTML=`<div class="stcard"><div class="locked">Leaderboards and storylines appear once matches are played.</div></div>`; return; }
 const scorers={}, ratingAcc={}, teamAcc={}, gkAcc={}, cardAcc={};
 let totalGoals=0;
 keys.forEach(k=>{
   const ev=D.goal_events[k], f=fxKey[k], score=matchScore(f,ev);
   totalGoals+=score[0]+score[1];
   const lu=D.lineups[k];
   // scorer names: prefer the lineup's goal events (reliable scorer name) over the score timeline (which can be unnamed)
   const luG = lu && lu.events ? lu.events.filter(e=>e.type==="goal" && !(e.detail||"").toLowerCase().includes("own")) : null;
   const goalList = (luG && luG.length) ? luG.map(e=>({name:e.player,team:e.team,pen:(e.detail||"").toLowerCase().includes("pen")}))
                    : (ev||[]).filter(e=>!e.og).map(e=>({name:e.name,team:e.team,pen:e.pen}));
   goalList.forEach(e=>{ if(!e.name)return; const t=e.team==="home"?f.home:f.away; const id=e.name+"|"+t;   // skip goals with no known scorer (no "undefined")
     const s=scorers[id]||(scorers[id]={name:e.name,team:t,goals:0,pens:0}); s.goals++; if(e.pen)s.pens++; });
   // full-model ratings when a lineup exists for this match; else goal-contributor fallback
   const rated = (lu && (lu.home||lu.away)) ? fullSquadRatings(lu,score) : playerRatings(ev,score);
   rated.forEach(r=>{ const t=r.team==="home"?f.home:f.away; const id=r.name+"|"+t;
     const a=ratingAcc[id]||(ratingAcc[id]={name:r.name,team:t,pos:r.pos||"",sum:0,n:0,best:0,goals:0,assists:0});
     a.sum+=r.rating; a.n++; a.best=Math.max(a.best,r.rating); a.goals+=r.goals||0; a.assists+=r.assists||0;
     const ta=teamAcc[t]||(teamAcc[t]={team:t,sum:0,n:0}); ta.sum+=r.rating; ta.n++;
   });
   if(lu){   // keepers (clean sheets / saves) + cards (fair play), from lineup data
     ["home","away"].forEach(t=>{ const b=lu[t]; if(!b)return; const tn=t==="home"?f.home:f.away; const conc=t==="home"?score[1]:score[0];
       const gk=(b.xi||[]).find(p=>(p.pos||"").toUpperCase()==="G");
       if(gk){ const id=gk.name+"|"+tn; const g=gkAcc[id]||(gkAcc[id]={name:gk.name,team:tn,cs:0,sv:0,gc:0,n:0});
         g.n++; g.gc+=conc; if(gk.st)g.sv+=+gk.st.SV||0; if(conc===0)g.cs++; } });
     (lu.events||[]).forEach(e=>{ if(e.type!=="card")return; const tn=e.team==="home"?f.home:f.away;
       const c=cardAcc[tn]||(cardAcc[tn]={team:tn,y:0,r:0}); e.card==="red"?c.r++:c.y++; });
   }
 });
 STATAGG={ratingAcc,gkAcc};   // shared with Team of the Tournament
 const boot=Object.values(scorers).sort((a,b)=>b.goals-a.goals||a.pens-b.pens).slice(0,8);
 const power=Object.values(ratingAcc).map(a=>({...a,avg:a.sum/a.n})).sort((a,b)=>b.avg-a.avg||b.best-a.best).slice(0,12);
 const teamRank=Object.values(teamAcc).map(a=>({...a,avg:a.sum/a.n})).sort((a,b)=>b.avg-a.avg);

 let upset=null, drama=null, hi=null, correct=0, ll=0, brier=0;
 keys.forEach(k=>{ const ev=D.goal_events[k], f=fxKey[k], score=scoreFromGE(ev);
   const pre=WCInPlay.probs(f.eh,f.ea,0,0,0);
   const favSide=pre[0]>=pre[2]?0:2, favProb=Math.max(pre[0],pre[2]);
   const actIdx=score[0]>score[1]?0:score[0]<score[1]?2:1;
   if(actIdx===pre.indexOf(Math.max(...pre))) correct++;
   ll += -Math.log(Math.max(pre[actIdx],1e-9));
   brier += [0,1,2].reduce((s,j)=>s+(pre[j]-(j===actIdx?1:0))**2,0);
   if(actIdx!==favSide){ if(!upset||favProb>upset.mag) upset={f,score,mag:favProb,
     favName:favSide===0?f.home:f.away, winName:actIdx===1?"Draw":(actIdx===0?f.home:f.away)}; }
   const full=Math.max(90,...ev.map(e=>e.min+(e.add||0))); const tl=WCInPlay.timeline(f.eh,f.ea,ev,full,redsOf(f)); let mx=0,mn=1; tl.forEach(p=>{mx=Math.max(mx,p.p[0]);mn=Math.min(mn,p.p[0]);});
   const sw=mx-mn; if(!drama||sw>drama.sw) drama={f,score,sw};
   const tot=score[0]+score[1]; if(!hi||tot>hi.tot) hi={f,score,tot};
 });
 const lbl=f=>`${F(f.home)} ${f.home} v ${f.away} ${F(f.away)}`;
 const tiles=[
   ["Biggest upset", upset?`${upset.winName==="Draw"?"Draw":F(upset.winName)+" "+upset.winName}`:"None yet",
     upset?`model backed ${upset.favName} at ${pc(upset.mag,0)} — ${upset.score[0]}–${upset.score[1]}`:"favourites holding"],
   ["Most dramatic", drama?`${pc(drama.sw,0)} swing`:"—", drama?lbl(drama.f)+` ${drama.score[0]}–${drama.score[1]}`:""],
   ["Highest scoring", hi?`${hi.tot} goals`:"—", hi?lbl(hi.f)+` ${hi.score[0]}–${hi.score[1]}`:""],
   ["Model accuracy", `${correct}/${keys.length}`, `results called correctly so far`],
   ["Model log-loss", (ll/keys.length).toFixed(3), `vs 1.099 coin-flip — lower is better`],
   ["Model Brier", (brier/keys.length).toFixed(3), `vs 0.667 coin-flip — lower is better`],
   ["Goals / match", (totalGoals/keys.length).toFixed(2), `${totalGoals} goals in ${keys.length} matches`],
   ["Matches played", `${keys.length}/72`, `group stage`],
 ].map(t=>`<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="d">${t[2]}</div></div>`).join("");

 const bootHTML=boot.map((s,i)=>`<div class="lbrow ${i===0?'lead':''}"><span class="rk">${i+1}</span><span class="gb">${F(s.team)}</span><span class="nm">${s.name}</span><span class="sub">${s.pens?s.pens+' pen':''}</span><span class="big">${s.goals}</span></div>`).join("");
 const powerHTML=power.map((s,i)=>{const ga=[s.goals?`${s.goals}⚽`:"",s.assists?`${s.assists}🅰`:""].filter(Boolean).join(" ");
   return `<div class="lbrow ${i===0?'lead':''}"><span class="rk">${i+1}</span><span class="gb">${F(s.team)}</span><span class="nm">${s.name} <span class="sub">${s.pos||""} ${ga}</span></span><span class="sub" title="matches">${s.n}m</span><span class="ratemini"><i style="width:${s.avg*10}%"></i></span><span class="big">${s.avg.toFixed(1)}</span></div>`;}).join("");
 const teamRankHTML=teamRank.map((s,i)=>`<div class="lbrow ${i===0?'lead':''}"><span class="rk">${i+1}</span><span class="gb">${F(s.team)}</span><span class="nm">${s.team}</span><span class="ratemini"><i style="width:${s.avg*10}%"></i></span><span class="big">${s.avg.toFixed(1)}</span></div>`).join("");

 const emptyLB=`<div class="lbrow"><span class="sub" style="padding:7px 4px">None yet.</span></div>`;
 const glove=Object.values(gkAcc).map(g=>({...g,svpct:(g.sv+g.gc)>0?g.sv/(g.sv+g.gc):0})).sort((a,b)=>b.cs-a.cs||b.svpct-a.svpct||b.sv-a.sv).slice(0,8);
 const assistL=Object.values(ratingAcc).filter(a=>a.assists>0).sort((a,b)=>b.assists-a.assists||b.goals-a.goals).slice(0,8);
 const fair=Object.values(cardAcc).map(c=>({...c,fp:c.y+c.r*3,tot:c.y+c.r})).sort((a,b)=>b.fp-a.fp||b.r-a.r).slice(0,8);
 const lbtag='style="font-size:9.5px;color:var(--blue);background:var(--blue-soft);border-radius:6px;padding:2px 7px"';
 const gloveHTML=glove.length?glove.map((g,i)=>`<div class="lbrow ${i===0?'lead':''}"><span class="rk">${i+1}</span><span class="gb">${F(g.team)}</span><span class="nm">${g.name} <span class="sub">${g.cs} CS · ${(g.svpct*100)|0}% sv · ${g.n}m</span></span><span class="big">${g.cs}</span></div>`).join(""):emptyLB;
 const assistHTML=assistL.length?assistL.map((a,i)=>`<div class="lbrow ${i===0?'lead':''}"><span class="rk">${i+1}</span><span class="gb">${F(a.team)}</span><span class="nm">${a.name} <span class="sub">${a.pos||""}</span></span><span class="big">${a.assists}</span></div>`).join(""):emptyLB;
 const fairHTML=fair.length?fair.map((c,i)=>`<div class="lbrow ${i===0?'lead':''}"><span class="rk">${i+1}</span><span class="gb">${F(c.team)}</span><span class="nm">${c.team}</span><span class="sub">${c.y?'🟨'+c.y+' ':''}${c.r?'🟥'+c.r:''}</span><span class="big">${c.tot}</span></div>`).join(""):emptyLB;
 box.innerHTML=`
  <div class="stwrap">
   <div class="stcard"><h3>🥇 Golden Boot</h3>${bootHTML}</div>
   <div class="stcard"><h3>⭐ Top performers <span ${lbtag}>avg rating · model v3</span></h3>${powerHTML}</div>
   <div class="stcard"><h3>🛡 Team rating table <span ${lbtag}>squad avg</span></h3>${teamRankHTML}</div>
  </div>
  <div class="stwrap" style="margin-top:16px">
   <div class="stcard"><h3>🧤 Golden Glove <span ${lbtag}>clean sheets · save%</span></h3>${gloveHTML}</div>
   <div class="stcard"><h3>🅰️ Assist King</h3>${assistHTML}</div>
   <div class="stcard"><h3>🟨 Discipline <span ${lbtag}>cards · fair play</span></h3>${fairHTML}</div>
  </div>
  <div class="stcard" style="margin-top:16px"><h3>📈 Storylines</h3><div class="tiles">${tiles}</div></div>`;
}

/* ---- Team of the Tournament: best XI by avg rating, laid out 4-3-3 ---- */
function renderBestXI(){
 const box=document.getElementById("bestxibox"); if(!box)return;
 const acc=(STATAGG&&STATAGG.ratingAcc)||{};
 const players=Object.values(acc).filter(a=>a.n>=1).map(a=>({...a,avg:a.sum/a.n,POS:(a.pos||"M").toUpperCase()}));
 if(players.length<11){ box.innerHTML=`<div class="locked">The Team of the Tournament builds as matches are played.</div>`; return; }
 const used=new Set(); const key=p=>p.name+"|"+p.team;
 const pick=(P,n)=>{const o=[]; players.filter(x=>x.POS===P).sort((a,b)=>b.avg-a.avg||b.n-a.n).forEach(x=>{ if(o.length<n&&!used.has(key(x))){o.push(x);used.add(key(x));} }); return o;};
 let gk=pick("G",1), df=pick("D",4), md=pick("M",3), fw=pick("F",3);
 const rest=players.filter(x=>x.POS!=="G"&&!used.has(key(x))).sort((a,b)=>b.avg-a.avg);
 while(gk.length+df.length+md.length+fw.length<11 && rest.length){ const p=rest.shift();
   if(df.length<4)df.push(p); else if(md.length<3)md.push(p); else if(fw.length<3)fw.push(p); else md.push(p); }
 if(!gk.length){ const any=players.filter(x=>!used.has(key(x))).sort((a,b)=>b.avg-a.avg)[0]; if(any)gk=[any]; }
 const xi=[...gk,...df,...md,...fw]; const avgX=xi.length?(xi.reduce((s,p)=>s+p.avg,0)/xi.length):0;
 const chip=p=>`<span class="pchip"><span class="phead" data-pl="${escAttr(p.name)}"><span class="pnum">${p.avg.toFixed(1)}</span></span><span class="pnm">${p.name}</span><span class="pnm" style="color:var(--mut);font-size:9px">${F(p.team)} ${p.avg.toFixed(2)}</span></span>`;
 const rows=[gk,df,md,fw].filter(r=>r.length).map(r=>`<div class="pline">${r.map(chip).join("")}</div>`).join("");
 box.innerHTML=`<div class="luhdr"><b>Best XI so far</b><span class="formtag">4-3-3 · squad avg ${avgX.toFixed(2)}</span></div><div class="pitch">${rows}</div>`;
 hydratePhotos(box);
}

/* ---- Power Rankings: all 48 teams by model strength (Elo) + live title odds & movement ---- */
function renderPower(out){
 const box=document.getElementById("powerbox"); if(!box)return;
 const ti=D.teaminfo||{}, base=D.baseline||{}, champ=(out&&out.champion)||{};
 const rows=D.teams.map(t=>{ const info=ti[t]||{}; const c=champ[t]||0; const b=(base[t]&&base[t].p_champion)||0;
   return {team:t, elo:info.elo||0, group:info.group||"", champ:c, d:c-b}; }).sort((a,b)=>b.elo-a.elo);
 const maxElo=Math.max(1,...rows.map(r=>r.elo));
 const mv=d=> d>0.003?`<span class="mv up">▲ ${pc(d,1)}</span>`:d<-0.003?`<span class="mv dn">▼ ${pc(-d,1)}</span>`:`<span class="mv fl">–</span>`;
 box.innerHTML=`<table class="big"><thead><tr><th>#</th><th>Team</th><th>Grp</th><th>Strength (Elo)</th><th>Champion</th><th>Δ vs forecast</th></tr></thead><tbody>`+
  rows.map((r,i)=>`<tr><td>${i+1}</td><td><span class="gb">${F(r.team)}</span> ${r.team}</td><td>${r.group}</td><td><span class="elobar"><i style="width:${(100*r.elo/maxElo).toFixed(0)}%"></i></span><b>${r.elo}</b></td><td>${pc(r.champ,1)}</td><td>${mv(r.d)}</td></tr>`).join("")+
  `</tbody></table>`;
}

/* ---- what-if simulator: overlay hypothetical group results, re-run the engine, show title-race shift ---- */
let WIF={}, WIF_BUILT=false;
function whatifScores(){ const m={H:[1,0],D:[1,1],A:[0,1]}, o={}; for(const fid in WIF) o[fid]=m[WIF[fid]]; return o; }
function runWhatIf(){
 const box=document.getElementById("wifimpact"); if(!box)return;
 if(!Object.keys(WIF).length){ box.innerHTML=`<div class="locked">Pick one or more results above to see how the title race shifts.</div>`; return; }
 const merged=Object.assign({}, whatifScores(), STATE.results);   // real results always win over hypotheticals
 const out=WCLive.runLive(D,{N:Math.min(NSIMS,30000), results:merged, ko:STATE.ko, seed:99});
 const baseC=(LAST&&LAST.champion)||{};
 const all=D.teams.map(t=>{const now=out.champion[t]||0, was=baseC[t]||0; return {t,now,d:now-was};});
 const movers=all.filter(x=>Math.abs(x.d)>0.0015).sort((a,b)=>b.d-a.d);
 const ups=movers.filter(x=>x.d>0).slice(0,6), dns=movers.filter(x=>x.d<0).sort((a,b)=>a.d-b.d).slice(0,6);
 const chip=x=>`<div class="wifm"><span class="gb">${F(x.t)}</span> ${x.t}<span class="wifd ${x.d>0?'up':'dn'}">${x.d>0?'▲':'▼'} ${pc(Math.abs(x.d),1)}</span><span class="wifnow">${pc(x.now,1)}</span></div>`;
 box.innerHTML=`<div class="wifcols"><div><div class="wifh up">Title chances rise</div>${ups.length?ups.map(chip).join(""):'<div class="locked">—</div>'}</div>`+
   `<div><div class="wifh dn">Title chances fall</div>${dns.length?dns.map(chip).join(""):'<div class="locked">—</div>'}</div></div>`+
   `<div class="heatcap">${Object.keys(WIF).length} hypothetical result(s) · ${Math.min(NSIMS,30000).toLocaleString()} tournaments re-simulated · Δ vs the live forecast</div>`;
}
function renderWhatIf(){
 if(WIF_BUILT) return;
 const box=document.getElementById("whatifbox"); if(!box)return;
 const rem=D.fixtures.filter(f=>!STATE.results[f.id] && !(STATE.live&&STATE.live[f.id]));
 if(!rem.length){ box.innerHTML=`<div class="locked">All group matches are decided — the what-if simulator returns for the knockout rounds.</div>`; WIF_BUILT=true; return; }
 const byG={}; rem.forEach(f=>{(byG[f.group]=byG[f.group]||[]).push(f);});
 const btn=(f,o,lbl)=>`<button data-fid="${f.id}" data-out="${o}" class="${WIF[f.id]===o?'on':''}">${lbl}</button>`;
 const row=f=>`<div class="wifrow"><span class="wift">${F(f.home)} ${f.home}</span><span class="wifbtns">${btn(f,'H','1')}${btn(f,'D','X')}${btn(f,'A','2')}</span><span class="wift a">${f.away} ${F(f.away)}</span></div>`;
 const groups=Object.keys(byG).sort().map(g=>`<div class="wifgrp"><div class="wifgl">Group ${g}</div>${byG[g].map(row).join("")}</div>`).join("");
 box.innerHTML=`<div class="wiftop"><span class="wifhint">1 = left team wins · X = draw · 2 = right team wins</span><button class="btn ghost" id="wifreset">Reset</button></div>`+
   `<div class="wifgrid">${groups}</div><div id="wifimpact" class="wifimpact"></div>`;
 box.querySelector(".wifgrid").addEventListener("click",e=>{ const b=e.target.closest("button[data-fid]"); if(!b)return;
   const fid=b.dataset.fid, o=b.dataset.out;
   if(WIF[fid]===o) delete WIF[fid]; else WIF[fid]=o;
   b.closest(".wifrow").querySelectorAll("button[data-fid]").forEach(x=>x.classList.toggle("on", WIF[x.dataset.fid]===x.dataset.out));
   runWhatIf();
 });
 document.getElementById("wifreset").onclick=()=>{ WIF={}; box.querySelectorAll("button[data-fid]").forEach(x=>x.classList.remove("on")); runWhatIf(); };
 runWhatIf();
 WIF_BUILT=true;
}

/* ---- model accuracy scorecard (model vs market vs coin-flip, on settled matches) ---- */
function hdaFromPmf(pm){ const G=D.grid; let h=0,d=0,a=0;
 for(let i=0;i<G;i++)for(let j=0;j<G;j++){const p=pm[i*G+j]||0; if(i>j)h+=p; else if(i===j)d+=p; else a+=p;}
 const s=h+d+a||1; return [h/s,d/s,a/s]; }
function _rps(p,o){ const c1=p[0],c2=p[0]+p[1],o1=o===0?1:0,o2=o<=1?1:0; return 0.5*((c1-o1)*(c1-o1)+(c2-o2)*(c2-o2)); }
function _ll(p,o){ return -Math.log(Math.max(1e-12,p[o])); }
function _brier(p,o){ let s=0; for(let k=0;k<3;k++){const t=k===o?1:0; s+=(p[k]-t)*(p[k]-t);} return s; }
function renderModelScore(){
 const box=document.getElementById("scorecardbox"); if(!box)return;
 const rows=[];
 D.fixtures.forEach(f=>{ const res=STATE.results[f.id]; if(!res)return; const pm=f.pmf||[]; if(!pm.length)return;
   const o=res[0]>res[1]?0:(res[0]===res[1]?1:2);
   const lu=D.lineups[f.home+"|"+f.away]; const mk=lu&&lu.market;
   rows.push({f,res,o,model:hdaFromPmf(pm),market:mk?[mk.h,mk.d,mk.a]:null}); });
 if(!rows.length){ box.innerHTML=`<div class="locked">The scorecard fills in as group matches are played.</div>`; return; }
 const agg=(sel,subset)=>{ let n=0,ll=0,rp=0,br=0,hit=0; (subset||rows).forEach(r=>{const p=sel(r); if(!p)return; n++; ll+=_ll(p,r.o); rp+=_rps(p,r.o); br+=_brier(p,r.o); const mx=Math.max(p[0],p[1],p[2]); if(p[r.o]===mx)hit++;}); return n?{n,ll:ll/n,rp:rp/n,br:br/n,hit:hit/n}:null; };
 const M=agg(r=>r.model);
 const U=agg(r=>[1/3,1/3,1/3]);
 const skill=(1-M.rp/U.rp);                                   // RPS skill score vs coin-flip
 const withMkt=rows.filter(r=>r.market);
 const Mh=withMkt.length?agg(r=>r.model,withMkt):null;        // model on the market-covered subset
 const K=withMkt.length?agg(r=>r.market,withMkt):null;        // the market itself
 const tile=(lbl,v,sub)=>`<div class="sctile"><div class="scv">${v}</div><div class="scl">${lbl}</div>${sub?`<div class="scs">${sub}</div>`:""}</div>`;
 let head=`<div class="scgrid">`+
   tile("matches scored",M.n)+
   tile("hit rate",pc(M.hit,0),"model's favourite won")+
   tile("RPS",M.rp.toFixed(3),"lower is better")+
   tile("log loss",M.ll.toFixed(3),`coin-flip ${U.ll.toFixed(3)}`)+
   tile("skill vs coin-flip",(skill>=0?"+":"")+pc(skill,0),"RPS improvement")+
   `</div>`;
 // head-to-head vs market
 let h2h="";
 if(Mh&&K){
   const dR=K.rp-Mh.rp;                                       // >0 => model better (lower RPS)
   const verdict = Math.abs(dR)<0.002 ? `<span class="callt">dead level with the market</span>`
     : dR>0 ? `<span class="callt ok">✓ model ahead of the market</span>` : `<span class="callt mkt">market ahead</span>`;
   const bar=(lbl,a,b,fmt)=>{const better=a<=b; return `<div class="scbar"><span class="scbl">${lbl}</span><span class="scbb"><i class="${better?'win':''}" style="width:${(100*a/Math.max(a,b)).toFixed(0)}%"></i></span><span class="scbv">${fmt(a)}</span></div>`;};
   h2h=`<div class="card mcsec" style="margin-top:14px"><h4>Model vs Market <span class="tag">${withMkt.length} matches with odds</span> ${verdict}</h4>`+
     `<div class="mvk"><div class="mvkside"><div class="mvkh">Our model</div>`+
       bar("RPS",Mh.rp,K.rp,v=>v.toFixed(3))+bar("Log loss",Mh.ll,K.ll,v=>v.toFixed(3))+bar("Hit rate",1-Mh.hit,1-K.hit,()=>pc(Mh.hit,0))+
     `</div><div class="mvkside"><div class="mvkh">Bookmaker market</div>`+
       bar("RPS",K.rp,Mh.rp,v=>v.toFixed(3))+bar("Log loss",K.ll,Mh.ll,v=>v.toFixed(3))+bar("Hit rate",1-K.hit,1-Mh.hit,()=>pc(K.hit,0))+
     `</div></div><div class="heatcap">Lower RPS / log loss = sharper, better-calibrated probabilities. Market implied from ESPN money lines (vig removed).</div></div>`;
 }
 // per-match table
 const lab=p=>["H","D","A"][p.indexOf(Math.max(p[0],p[1],p[2]))];
 const pick=(r,p)=> p ? `${lab(p)==="H"?F(r.f.home)+" "+r.f.home:lab(p)==="A"?F(r.f.away)+" "+r.f.away:"Draw"} <span class="pkpc">${pc(Math.max(p[0],p[1],p[2]),0)}</span>` : "—";
 const okmark=(p,o)=> p ? (p.indexOf(Math.max(p[0],p[1],p[2]))===o?`<span class="okp">✓</span>`:`<span class="nop">✗</span>`) : "";
 let list=`<div class="card tscroll" style="margin-top:14px"><table class="big sctab"><thead><tr><th>Match</th><th>Result</th><th>Model pick</th><th></th><th>Market pick</th><th></th></tr></thead><tbody>`+
   rows.slice().reverse().map(r=>{const m=r.model,k=r.market;
     return `<tr><td>${F(r.f.home)} ${r.f.home} v ${r.f.away} ${F(r.f.away)}</td><td><b>${r.res[0]}–${r.res[1]}</b></td><td>${pick(r,m)}</td><td>${okmark(m,r.o)}</td><td>${pick(r,k)}</td><td>${okmark(k,r.o)}</td></tr>`;}).join("")+
   `</tbody></table></div>`;
 box.innerHTML=head+h2h+list;
}

/* ---- status bar ---- */
let statusMode="idle";
function setStatus(m){statusMode=m;renderStatus();}
function renderStatus(){
 const sb=document.getElementById("statusbar");
 const connected=STATE.source==="espn"||STATE.source==="live";
 const srcDot=connected?'<span class="dot ok"></span>':'<span class="dot warn"></span>';
 const srcTxt=STATE.source==="espn"?('<b>ESPN live</b> connected'+(STATE.liveCount?' · '+STATE.liveCount+' live now':'')):STATE.source==="live"?'<b>Live feed</b> connected':'<b>Offline snapshot</b> (feed blocked)';
 const upd=STATE.fetchedUTC?fmtTime.format(STATE.fetchedUTC):"—";
 const busy=statusMode==="sim"?'<span class="pill"><span class="spin"></span> simulating '+NSIMS.toLocaleString()+' tournaments…</span>'
           :statusMode==="loading"?'<span class="pill"><span class="spin"></span> fetching results…</span>':'';
 sb.innerHTML=
  `<span class="pill">${srcDot}${srcTxt}</span>`+
  `<span class="pill"><b>${STATE.played}</b>/72 group matches played</span>`+
  `<span class="pill">updated <b>${upd}</b> · ${tzAbbr}${(AUTO&&STATE.liveCount>0)?' · auto every 25s':''}</span>`+
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
 return D.fixtures.filter(f=>f.utc && !STATE.results[f.id] && !(STATE.live&&STATE.live[f.id]) && new Date(f.utc).getTime()>now-2*3600e3)
  .sort((a,b)=>new Date(a.utc)-new Date(b.utc)); }
function renderFeed(){
 const now=Date.now();
 const items=D.fixtures.map(f=>{
  const r=STATE.results[f.id]; const lv=STATE.live&&STATE.live[f.id]; const t=f.utc?new Date(f.utc).getTime():null;
  const wallLive = STATE.source!=="espn" && t && now>=t && now<t+2.5*3600e3;   // clock guess only when ESPN status is unavailable
  let status= r?"ft":((lv||wallLive)?"live":"upcoming");
  return {f,r,lv,t,status,key:f.utc?fmtDayKey.format(new Date(f.utc)):f.id};
 }).sort((a,b)=>(a.t||0)-(b.t||0));
 const byDay={};
 items.forEach(it=>{(byDay[it.key]=byDay[it.key]||[]).push(it);});
 const today=fmtDayKey.format(new Date());
 const box=document.getElementById("feedbox"); box.innerHTML="";
 Object.keys(byDay).sort().forEach(k=>{
  const its=byDay[k]; const d=its[0].f.utc?new Date(its[0].f.utc):null;
  const label=d?fmtDayLong.format(d)+(k===today?" · TODAY":""):"";
  const cards=its.map(({f,r,lv,status})=>{
   const time=f.utc?fmtTime.format(new Date(f.utc)):"";
   const sc=r||(lv?[lv.hs,lv.as]:null);
   const stTxt=status==="ft"?"FULL TIME":status==="live"?(lv&&lv.minute!=null?("● "+lv.minute+"'"):"● LIVE"):time;
   const rowsHTML=[[f.home,sc?sc[0]:null],[f.away,sc?sc[1]:null]].map(([t,s],i)=>{
     const other=sc?sc[1-i]:null; const cls=sc?(s>other?"win":s<other?"lose":""):"";
     return `<div class="mrow ${cls}"><span>${F(t)}</span><span class="nm">${t}</span><span class="sc">${s==null?"":s}</span></div>`;
   }).join("");
   const interactive = status!=="upcoming";
   const chip = interactive ? `<div style="text-align:right;margin-top:5px"><span class="wpchip">📈 WIN PROBABILITY</span></div>` : "";
   return `<div class="mcard ${interactive?"clk":""} ${status}" ${interactive?`data-fid="${f.id}"`:""}><div class="top"><span>Group ${f.group} · ${f.city}</span><span class="st ${status}">${stTxt}</span></div>${rowsHTML}${chip}</div>`;
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
  const N3=p=>p==null?"–":(p*100)|0;
  const scen=D.groups[g].map(t=>{ const adv=out.r32[t]||0, c=out.cond&&out.cond[t];
    let tag,cls="hunt";
    if(adv>=0.999){tag="Through";cls="thru";}
    else if(adv<=0.001){tag="Out";cls="out";}
    else if(!c||c.win.p==null){tag=adv>=0.5?"Favoured":"Long shot";}
    else if(c.draw.p>=0.985){tag="A point is enough";}
    else if(c.win.p>=0.97){tag="Win to qualify";}
    else if(c.win.p<0.85){tag="Win and hope";}
    else {tag="In contention";}
    const s3=(c&&c.win.p!=null)?`<span class="sc3">W <b>${N3(c.win.p)}</b> · D <b>${N3(c.draw.p)}</b> · L <b>${N3(c.lose.p)}</b></span>`:"";
    return `<div class="scenrow"><span class="gb">${F(t)}</span><span class="snm">${t}</span><span class="stag ${cls}">${tag}</span>${s3}</div>`;
  }).join("");
  const scenBlock = played<6 ? `<div class="scen"><div class="scenh">Who needs what · next match (% to advance)</div>${scen}</div>` : "";
  box.insertAdjacentHTML("beforeend",
   `<div class="gcard"><h3><span>GROUP ${g}</span><span>${played}/6 played</span></h3>
    <table class="gt"><thead><tr><th>Team</th><th>Pld</th><th>Pts</th><th>GD</th><th>Advance</th></tr></thead>
    <tbody>${rows}</tbody></table>${scenBlock}</div>`);
 }
}

/* ---- odds table ---- */
function renderOdds(out){
 const rows=Object.keys(out.champion).map(t=>({t,...out})).map(o=>({
   team:o.t,champ:out.champion[o.t],fin:out.final[o.t],sf:out.sf[o.t],qf:out.qf[o.t],r16:out.r16[o.t],r32:out.r32[o.t],
   d:out.champion[o.t]-D.baseline[o.t].p_champion}))
  .sort((a,b)=>b.champ-a.champ);
 const tb=document.querySelector("#oddstable tbody");
 tb.innerHTML=rows.map((r,i)=>`<tr data-team="${r.team}">
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
 const ms = (STATE.liveCount>0) ? 25000 : 90000;   // poll ESPN faster while a match is in play
 autoTimer=setTimeout(()=>{loadLive().then(scheduleAuto);},ms); }

document.getElementById("ftN").textContent=NSIMS.toLocaleString();
loadLive().then(scheduleAuto);

/* ===== Win-probability explorer ===== */
const WP={fid:null,events:[],reds:[],minute:90,anim:null,mode:"actual",followLive:false};
// red-card events for a fixture (from the lineup feed) — drive the man-advantage in the in-play model
function redsOf(f){ const lu=D.lineups[f.home+"|"+f.away]; if(!lu||!lu.events)return [];
 return lu.events.filter(e=>e.type==="card"&&e.card==="red").map(e=>({min:e.min,add:e.add||0,team:e.team})); }
// home/away shots on target so far (live xG proxy) from team stats, or null
function sotOf(f){ const lu=D.lineups[f.home+"|"+f.away]; const ts=lu&&lu.teamstats; if(!ts)return null;
 const g=s=>{const v=s&&s.shotsOnTarget; const n=parseInt(String(v==null?"":v),10); return isNaN(n)?null:n;};
 const h=g(ts.home), a=g(ts.away); return (h==null||a==null)?null:{hsot:h,asot:a}; }
const ov=document.getElementById("wpov"), modalEl=document.getElementById("wpmodal");
function mulberry(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}

/* team detail modal — odds, recent form, all-time head-to-head */
const tmov=document.getElementById("tmov"), tmmodal=document.getElementById("tmmodal");
function closeTeam(){ tmov.classList.remove("show"); document.body.style.overflow=""; }
tmov.addEventListener("click",e=>{ if(e.target===tmov) closeTeam(); });
function openTeam(team){
 const ti=D.teaminfo[team]; if(!ti) return;
 const o=LAST||{}; const g=ti.group;
 const rivals=(D.groups[g]||[]).filter(t=>t!==team);
 const formHTML=(D.form[team]||[]).map(m=>`<div class="frow"><span class="res ${m.res}">${m.res}</span><span style="flex:1">vs ${F(m.opp)} ${m.opp}</span><span class="sc">${m.gf}–${m.ga}</span></div>`).join("")||`<div class="locked">No recent matches.</div>`;
 const h2hHTML=rivals.map(opp=>{ const rec=(D.h2h[team]||{})[opp];
   if(!rec) return `<div class="h2hrow"><span class="opp">${F(opp)} ${opp}</span><span class="wdl">never met</span></div>`;
   const [w,d,l,gf,ga]=rec; return `<div class="h2hrow"><span class="opp">${F(opp)} ${opp}</span><span class="wdl">${w}W ${d}D ${l}L · ${gf}–${ga}</span></div>`;
 }).join("");
 const odds = o.champion ? `<div class="tmstats">
   <div class="b"><div class="v">${pc(o.champion[team],1)}</div><div class="k">Champion</div></div>
   <div class="b"><div class="v">${pc(o.final[team],1)}</div><div class="k">Final</div></div>
   <div class="b"><div class="v">${pc(o.qf[team])}</div><div class="k">Quarters</div></div>
   <div class="b"><div class="v">${pc(o.r32[team])}</div><div class="k">Advance</div></div>
   <div class="b"><div class="v">${ti.elo}</div><div class="k">Elo</div></div></div>` : "";
 tmmodal.innerHTML=`
  <button class="close" id="tmclose" aria-label="Close">✕</button>
  <div class="mh"><span class="tn">${F(team)} ${team}</span></div>
  <div class="meta">Group ${g} · model attack ${ti.attack} · defence ${ti.defence}</div>
  ${odds}
  <div class="mcsec" style="margin-top:14px"><h4>Recent form <span class="tag">last ${(D.form[team]||[]).length}</span></h4>${formHTML}</div>
  <div class="mcsec" style="margin-top:14px"><h4>Head-to-head vs group rivals <span class="tag">all-time · 1872–2026</span></h4>${h2hHTML}</div>`;
 tmov.classList.add("show"); document.body.style.overflow="hidden";
 document.getElementById("tmclose").onclick=closeTeam;
}

function matchStatus(fid){
 const f=fixById[fid]; const res=STATE.results[fid];
 if(res) return "ft";
 if(STATE.live&&STATE.live[fid]) return "live";   // ESPN says in-progress — authoritative
 if(STATE.source!=="espn"){                        // only guess "live" from the clock when ESPN status is unavailable
   const t=f.utc?new Date(f.utc).getTime():null;
   if(t && Date.now()>=t) return "live";
 }
 return "upcoming";
}
function openMatch(fid){
 const f=fixById[fid]; if(!f) return;
 WP.fid=fid; stopAnim();
 const res=STATE.results[fid];
 const known=D.goal_events[f.home+"|"+f.away];
 WP.status=matchStatus(fid);
 WP.reds=redsOf(f);                    // red cards drive the man-advantage in the win-prob model
 WP.followLive=(WP.status==="live");   // a freshly-opened live match auto-tracks new goals
 if(WP.status==="ft"){
   WP.events = known ? known.map(e=>({...e})) : (res ? spreadGoals(res[0],res[1]) : []);
   WP.full = matchFull(); WP.minute = WP.full;   // ends at the last goal (>=90), locked there
 } else if(WP.status==="live"){
   WP.events = known ? known.map(e=>({...e})) : [];   // real ESPN goals if available, else 0-0 baseline
   const lv=STATE.live&&STATE.live[fid]; const added=(lv&&lv.added)||0;
   if(lv && lv.minute!=null){ const m=Math.max(0,Math.min(90,lv.minute)); WP.minute = (m>=90 && added>0) ? 90+added : m; }   // 90'+x extends; 45'+x stays first-half
   else { const t=new Date(f.utc).getTime(); WP.minute = Math.max(0, Math.min(90, Math.round((Date.now()-t)/60000))); }
   WP.full = matchFull();
 } else {
   WP.events=[]; WP.minute=0; WP.full=90;              // upcoming: no fabricated story
 }
 ov.classList.add("show"); document.body.style.overflow="hidden";
 drawModal();
}
function spreadGoals(h,a){const ev=[];const tot=h+a;let i=0;
 for(let k=0;k<h;k++)ev.push({min:Math.round((++i)*90/(tot+1)),team:"home"});
 for(let k=0;k<a;k++)ev.push({min:Math.round((++i)*90/(tot+1)),team:"away"});
 return ev.sort((x,y)=>x.min-y.min);}
function closeModal(){ov.classList.remove("show");document.body.style.overflow="";stopAnim();}
ov.addEventListener("click",e=>{if(e.target===ov)closeModal();});
addEventListener("keydown",e=>{if(e.key==="Escape")closeModal();});

function xMap(m,FM){FM=FM||90; return 52+(m/FM)*(1000-52-72);}
function yMap(p){return 18+(1-p)*(360-18-30);}
function buildChart(f){
 const FM=WP.full||90;
 const T=WCInPlay.timeline(f.eh,f.ea,WP.events,FM,WP.reds);
 const line=(sel)=>T.map(pt=>xMap(pt.m,FM)+","+yMap(pt.p[sel])).join(" ");
 const grid=[0,.25,.5,.75,1].map(v=>`<line class="gridln" x1="52" y1="${yMap(v)}" x2="928" y2="${yMap(v)}"/><text class="axt" x="44" y="${yMap(v)+4}" text-anchor="end">${v*100|0}%</text>`).join("");
 const ticks=[1,15,30,45,60,75,90].filter(m=>m<=FM); if(WP.status!=="live" && FM>90.5)ticks.push(Math.round(FM));   // label the true end only when finished (live tail is model padding)
 const xt=ticks.map(m=>`<text class="axt" x="${xMap(m,FM)}" y="352" text-anchor="middle">${m>90?"90+"+(m-90):m}'</text>`).join("");
 const lu=D.lineups[f.home+"|"+f.away];
 const goals=WP.events.map(e=>{const gm=e.min+(e.add||0); const c=e.team==='home'?'var(--g2)':'var(--g3)'; const tag=e.og?" (OG)":e.pen?" (pen)":"";
   return `<g><title>${e.min}${e.add?'+'+e.add:''}' — ${F(e.team==='home'?f.home:f.away)} ${(e.name||'goal')}${tag}</title>
    <line x1="${xMap(gm,FM)}" y1="18" x2="${xMap(gm,FM)}" y2="330" stroke="${c}" stroke-width="1" stroke-dasharray="2 3" opacity=".5"/>
    <circle cx="${xMap(gm,FM)}" cy="14" r="3.6" fill="${c}"/></g>`;}).join("");
 const cards=(lu&&lu.events?lu.events.filter(e=>e.type==="card"):[]).map(e=>{const cm=e.min+(e.add||0); const col=e.card==="red"?"#e0322b":"#f5c518";
   return `<g><title>${e.min}' ${F(e.team==='home'?f.home:f.away)} ${e.player||""} — ${e.card} card</title><rect x="${(xMap(cm,FM)-2).toFixed(1)}" y="328" width="4" height="8" rx="1" fill="${col}"/></g>`;}).join("");
 const nowX=xMap(WP.minute,FM);
 const cur=T[WP.minute].p;
 const nowMarks=`<line x1="${nowX}" y1="14" x2="${nowX}" y2="330" stroke="var(--txt)" stroke-width="1.5" opacity=".5"/>`+
  [[0,'var(--g2)'],[1,'#9aa3b2'],[2,'var(--g3)']].map(([s,c])=>`<circle cx="${nowX}" cy="${yMap(cur[s])}" r="4" fill="${c}" stroke="var(--surface)" stroke-width="1.5"/>`).join("");
 const endLbl=(sel,c,txt)=>{const p=T[T.length-1].p[sel];return `<text x="934" y="${yMap(p)+4}" class="axt" fill="${c}" font-weight="700">${txt}</text>`;};
 return `<svg viewBox="0 0 1000 360" preserveAspectRatio="xMidYMid meet">
  ${grid}${xt}${goals}${cards}
  <polyline fill="none" stroke="#9aa3b2" stroke-width="2" stroke-dasharray="5 4" points="${line(1)}"/>
  <polyline fill="none" stroke="var(--g3)" stroke-width="2.5" points="${line(2)}"/>
  <polyline fill="none" stroke="var(--g2)" stroke-width="2.5" points="${line(0)}"/>
  ${nowMarks}
  ${endLbl(0,'var(--g2)','H')}${endLbl(1,'#9aa3b2','D')}${endLbl(2,'var(--g3)','A')}
 </svg>`;
}
function readouts(f,p){
 return `<div class="wpreadout">
   <div class="wpr h"><div class="v">${pc(p[0],1)}</div><div class="k">${f.home} win</div></div>
   <div class="wpr d"><div class="v">${pc(p[1],1)}</div><div class="k">Draw</div></div>
   <div class="wpr a"><div class="v">${pc(p[2],1)}</div><div class="k">${f.away} win</div></div>
  </div>`;
}

/* Our own player-rating model — scored entirely from real match events.
 * Base 6.8, +1.6 per open-play goal, +1.1 per penalty goal, -1.7 per own goal,
 * brace/hat-trick bonuses, small bump for contributing to a win. 4.0–10.0. */
function playerRatings(events, score){
 const by={};
 events.forEach(e=>{
  const playerTeam = e.og ? (e.team==="home"?"away":"home") : e.team;  // OG scorer is on conceding side
  const nm=e.name||"—", k=nm+"|"+playerTeam;
  const s=by[k]||(by[k]={name:nm,team:playerTeam,goals:0,pens:0,og:0});
  if(e.og) s.og++; else { s.goals++; if(e.pen) s.pens++; }
 });
 const hW=score[0]>score[1], aW=score[1]>score[0];
 return Object.values(by).map(s=>{
  let r=6.8 + 1.6*(s.goals-s.pens) + 1.1*s.pens - 1.7*s.og;
  if(s.goals>=3) r+=0.9; else if(s.goals===2) r+=0.5;
  if(((s.team==="home"&&hW)||(s.team==="away"&&aW)) && s.goals>0) r+=0.3;
  return {...s, rating:Math.max(4,Math.min(10,Math.round(r*10)/10))};
 }).sort((a,b)=>b.rating-a.rating || b.goals-a.goals);
}

const RNORM=s=>(s||"").normalize("NFKD").replace(/[̀-ͯ]/g,"").toLowerCase().trim();
function findStat(stat,name){const n=RNORM(name);return Object.values(stat).find(s=>RNORM(s.name)===n)||Object.values(stat).find(s=>RNORM(s.name).includes(n)&&n);}

/* ===========================================================================
 * PLAYER RATING MODEL v2 — position-aware, multi-factor.
 *   Anchored at 6.5 (a league-average performance), bounded 3.0–10.0.
 *   Goals/assists/cards come from match events; volume & defensive work
 *   (shots, shots on target, fouls, offsides, saves, goals conceded) come
 *   from real per-player ESPN stats. Every rating keeps a `breakdown` of the
 *   weighted contributions so it can be inspected on tap. Weights below were
 *   hand-tuned to land "average" outings near 6.5 and standout games near 8–9,
 *   matching the feel of WhoScored/SofaScore-style models.
 * ========================================================================== */
const RW={ goal:1.25, pen:0.85, brace:0.40, hat:1.00, assist:0.75,
  shot:0.02, shotCap:0.10, sot:0.10, sotCap:0.45, wasteful:-0.25,
  og:-1.60, miss:-0.70, foulC:-0.05, foulCcap:-0.35, foulS:0.04, foulScap:0.28,
  offside:-0.06, offCap:-0.25, yel:-0.30, red:-1.25,
  save:0.16, saveCap:1.30, svPct:2.60, svPctCap:1.10, gkConcede:-0.24, cleanGK:0.70,
  cleanDef:0.45, defConcede:-0.18, csPressure:0.04, csPressureCap:0.45,
  winStart:0.25, drawStart:0.05 };
const clampR=x=>Math.max(3,Math.min(10,Math.round(x*10)/10));
function togRate(el){const d=el.nextElementSibling; if(d&&d.classList.contains("rdet")){d.classList.toggle("open"); el.classList.toggle("ropen");}}
const cap=(v,lo,hi)=>Math.max(lo===null?-1e9:lo,Math.min(hi===null?1e9:hi,v));

/* Full-squad ratings from a lineup + events + per-player stats (our model v2). */
function fullSquadRatings(lu, score){
 const conceded={home:score[1],away:score[0]};
 const won={home:score[0]>score[1],away:score[1]>score[0]}, drew=score[0]===score[1];
 const stat={};
 const ensure=(t,name,pos,num,started,aid)=>{const k=t+"|"+name; return stat[k]||(stat[k]={team:t,name,pos:(pos||"").toUpperCase(),num:num,goals:0,pens:0,assists:0,og:0,yel:0,red:0,missed:0,on:false,off:false,started,st:null,aid:aid||null});};
 ["home","away"].forEach(t=>{const b=lu[t]; if(!b)return;
   (b.xi||[]).forEach(p=>{const s=ensure(t,p.name,p.pos,p.num,true,p.aid); if(p.st)s.st=p.st;});
   (b.subs||[]).forEach(p=>{const s=ensure(t,p.name,p.pos,p.num,false,p.aid); if(p.st)s.st=p.st;});});
 (lu.events||[]).forEach(e=>{
   if(e.type==="goal"){const d=(e.detail||"").toLowerCase();
     const s=findStat(stat,e.player);
     if(d.includes("own")){ if(s)s.og++; }
     else if(d.includes("miss")){ if(s)s.missed++; }
     else { if(s){s.goals++; if(d.includes("pen"))s.pens++;} const a=e.assist&&findStat(stat,e.assist); if(a)a.assists++; }
   } else if(e.type==="card"){const s=findStat(stat,e.player); if(s){e.card==="red"?s.red++:s.yel++;}}
   else if(e.type==="subst"){const onP=e.assist&&findStat(stat,e.assist); const offP=findStat(stat,e.player); if(onP){onP.on=true;onP.onMin=e.min;} if(offP){offP.off=true;offP.offMin=e.min;}}
 });
 const ts=lu.teamstats||{};
 const Nts=v=>{const x=parseFloat(String(v).replace(/[^0-9.\-]/g,""));return isNaN(x)?0:x;};
 const oppShots=t=>{ const o=(t==="home")?ts.away:ts.home; return (o&&o.totalShots!=null)?Nts(o.totalShots):null; };   // shots the team faced (defensive workload)
 return Object.values(stat).filter(s=>s.started||s.on).map(s=>{
   const bd=[]; const base=s.started?6.6:6.5;   // anchored near a real match average (~6.7)
   const add=(k,v)=>{ if(v) bd.push({k,v:Math.round(v*100)/100}); };
   const og=s.goals-s.pens;
   add("Goals",RW.goal*og); add("Penalty goals",RW.pen*s.pens);
   if(s.goals>=3)add("Hat-trick",RW.hat); else if(s.goals===2)add("Brace",RW.brace);
   add("Assists",RW.assist*s.assists);
   add("Own goal",RW.og*s.og); add("Missed penalty",RW.miss*s.missed);
   add("Yellow card",RW.yel*s.yel); add("Red card",RW.red*s.red);
   const st=s.st||{}, has=!!s.st;
   const SH=+st.SH||0, SOT=+st.SOT||0, nonGoalSOT=Math.max(0,SOT-s.goals);
   if(has){
     add("Shot volume",cap(RW.shot*SH,0,RW.shotCap));
     add("Shots on target",cap(RW.sot*nonGoalSOT,0,RW.sotCap));
     if(SH>=4 && SOT===0 && s.goals===0) add("Wasteful shooting",RW.wasteful);   // lots of shots, none on target
     add("Fouls committed",cap(RW.foulC*(+st.FC||0),RW.foulCcap,0));
     add("Fouls won",cap(RW.foulS*(+st.FS||0),0,RW.foulScap));
     if(s.pos==="F"||s.pos==="M") add("Offsides",cap(RW.offside*(+st.OFF||0),RW.offCap,0));
   }
   if(s.pos==="G"){
     const SV=+st.SV||0; const gc = has && st.GC!=null ? (+st.GC||0) : (s.started?conceded[s.team]:0);
     const sotFaced=SV+gc;                                                        // on-target shots faced ≈ saves + conceded
     add("Saves",cap(RW.save*SV,0,RW.saveCap));
     if(sotFaced>=3) add("Shot-stopping",cap((SV/sotFaced-0.70)*RW.svPct,-RW.svPctCap,RW.svPctCap));   // save % — the strongest GK signal
     add("Goals conceded",RW.gkConcede*gc);
     if(s.started&&conceded[s.team]===0){ const sf=(+st.SF||sotFaced); add("Clean sheet",RW.cleanGK+cap((sf-3)*RW.csPressure,0,RW.csPressureCap)); }   // worth more under fire
   } else if(s.pos==="D"){
     if(s.started&&conceded[s.team]===0){ const op=oppShots(s.team); add("Clean sheet",RW.cleanDef+(op!=null?cap((op-7)*RW.csPressure,0,RW.csPressureCap):0)); }
     else if(conceded[s.team]>=2) add("Heavy concession",RW.defConcede*(conceded[s.team]-1));
   }
   if(s.started){ if(won[s.team])add("Team won",RW.winStart); else if(drew)add("Team drew",RW.drawStart); }
   const rating=clampR(base + bd.reduce((a,x)=>a+x.v,0));
   return {team:s.team,name:s.name,pos:s.pos,num:s.num,started:s.started,on:s.on,off:s.off,onMin:s.onMin,offMin:s.offMin,
     goals:s.goals,assists:s.assists,pens:s.pens,og:s.og,yel:s.yel,red:s.red,
     rating, base, breakdown:bd};
 }).sort((a,b)=>b.rating-a.rating);
}

/* One-line Player-of-the-Match justification from the top positive drivers. */
function potmLine(r){
 const pos=(r.breakdown||[]).filter(b=>b.v>0).sort((a,b)=>b.v-a.v).slice(0,3).map(b=>b.k.toLowerCase());
 if(!pos.length) return "steady, error-free outing";
 const map={"goals":"goalscoring","penalty goals":"penalty","shots on target":"goal threat","shot volume":"attacking volume",
   "assists":"creativity","saves":"shot-stopping","clean sheet":"a clean sheet","team won":"a winning display","fouls won":"drawing fouls"};
 return pos.map(k=>map[k]||k).join(", ");
}

function matchCentre(f){
 const ev=WP.events;
 const res=STATE.results[WP.fid];
 const score = (WP.status==="ft" && res) ? res : WCInPlay.scoreAt(ev, WP.status==="live"?WP.minute:(WP.full||90));
 const teamName=t=>t==="home"?f.home:f.away;
 const lu=D.lineups[f.home+"|"+f.away];

 // pre-match score-distribution heatmap (rows = home goals, cols = away goals)
 const G=D.grid, NN=6, pm=f.pmf||[];
 let heatHTML="";
 if(pm.length){
  let mp=0; for(let i=0;i<NN;i++)for(let j=0;j<NN;j++) mp=Math.max(mp,pm[i*G+j]||0);
  let g=`<div class="heat" style="grid-template-columns:16px repeat(${NN},1fr)"><div></div>`+
    Array.from({length:NN},(_,j)=>`<div class="heatlbl">${j}</div>`).join("");
  for(let i=0;i<NN;i++){ g+=`<div class="heatlbl">${i}</div>`;
   for(let j=0;j<NN;j++){ const p=pm[i*G+j]||0, a=mp?p/mp:0;
     const act=(score[0]===i&&score[1]===j);
     g+=`<div class="heatcell ${act?"act":""}" style="background:rgba(30,111,217,${(0.06+0.92*a).toFixed(2)})">${p>=0.04?Math.round(p*100):""}</div>`; }
  }
  g+=`</div><div class="heatcap">Rows = ${F(f.home)} ${f.home} goals · columns = ${F(f.away)} ${f.away} goals · gold ring = actual result</div>`;
  heatHTML=`<div class="mcsec"><h4>Model score forecast <span class="tag">pre-match probabilities</span></h4>${g}</div>`;
 }

 // ---- goal log (always, from openfootball goal events) ----
 const golHTML = ev.length ? `<div class="golog">`+ev.slice().sort((a,b)=>a.min-b.min).map(e=>{
   const pt = e.og ? (e.team==="home"?"away":"home") : e.team;
   const bdg = e.og?`<span class="bdg og">OG</span>`:(e.pen?`<span class="bdg pen">PEN</span>`:"");
   return `<div class="gol"><span class="mn">${e.min}${e.add?'+'+e.add:''}'</span><span class="ic">⚽</span><span class="nm">${F(teamName(pt))} ${e.name||"—"}</span>${bdg}</div>`;
  }).join("")+`</div>` : `<div class="locked">No goals ${WP.status==="live"?"yet":"in this match"}.</div>`;

 // ---- ratings: full squad if lineup present, else goal contributors ----
 let ratHTML, ratTag;
 if(lu && (lu.home||lu.away)){
  ratTag="our model v2 · full squad · tap a player";
  const rows=fullSquadRatings(lu, score);
  const potm=rows.find(s=>s.rating>=7)||null;
  const bdHTML=s=>{
    const chips=[`<span class="bdchip base">Base ${s.base.toFixed(1)}</span>`]
      .concat((s.breakdown||[]).map(b=>`<span class="bdchip ${b.v>=0?'pos':'neg'}">${b.k} ${b.v>=0?'+':''}${b.v.toFixed(2)}</span>`));
    return `<div class="rdet">${chips.join("")}<span class="bdchip tot">= ${s.rating.toFixed(1)}</span></div>`;
  };
  const ratTags=s=>{const o=[];
    if(s.goals)o.push(`<span class="tg g" title="Goals">⚽${s.goals>1?'×'+s.goals:''}</span>`);
    if(s.assists)o.push(`<span class="tg a" title="Assists">A${s.assists>1?'×'+s.assists:''}</span>`);
    if(s.yel)o.push(`<span class="tg cd y" title="Yellow card"></span>`);
    if(s.red)o.push(`<span class="tg cd r" title="Red card"></span>`);
    if(s.og)o.push(`<span class="tg og" title="Own goal">OG</span>`);
    if(!s.started&&s.on)o.push(`<span class="tg subon" title="Came on as substitute${s.onMin?" at "+s.onMin+"'":""}">▲${s.onMin?" "+s.onMin+"'":" SUB"}</span>`);
    else if(s.started&&s.off)o.push(`<span class="tg suboff" title="Substituted off${s.offMin?" at "+s.offMin+"'":""}">▼${s.offMin?" "+s.offMin+"'":""}</span>`);
    return o.join("");};
  const POS={G:"GK",D:"DEF",M:"MID",F:"FWD"};
  const block=t=>{const rs=rows.filter(s=>s.team===t); if(!rs.length)return"";
    return `<div class="rteam"><span class="rtflag">${F(teamName(t))}</span> ${teamName(t)}</div>`+rs.map(s=>{
     const cls=s.rating>=8?"r-hi":s.rating>=7?"r-mid":"r-lo";
     const pc2=(s.pos||"").toUpperCase();
     const star=(s===potm)?`<span class="potm sm" title="Player of the Match">★</span>`:"";
     return `<div class="rrow ${cls}" onclick="togRate(this)"><span class="pos pos-${pc2||'X'}">${POS[pc2]||"–"}</span><span class="nm">${s.name}${star}</span><span class="tags">${ratTags(s)}</span><span class="rbar"><i style="width:${s.rating*10}%"></i></span><span class="rv">${s.rating.toFixed(1)}</span><span class="rcar">›</span></div>${bdHTML(s)}`;
    }).join("");};
  const potmHTML = potm ? `<div class="potmbar"><span class="potm">★ Player of the Match</span><b>${potm.name}</b> <span class="pm">${F(teamName(potm.team))} ${teamName(potm.team)} · ${potm.rating.toFixed(1)}</span><span class="why">— ${potmLine(potm)}</span></div>` : "";
  ratHTML=potmHTML+`<div class="rlist">${block("home")}${block("away")}</div>`;
 } else {
  ratTag="our model · goal contributors";
  const rows=playerRatings(ev, score);
  ratHTML = rows.length ? `<div class="rlist">`+rows.map((s,i)=>{
    const cls=s.rating>=8?"r-hi":s.rating>=7?"r-mid":"r-lo";
    const tags=[s.goals?`${s.goals}⚽`:"",s.pens?`${s.pens} pen`:"",s.og?`${s.og} OG`:""].filter(Boolean).join(" · ");
    const star=i===0&&s.goals>0?`<span class="potm">★ POTM</span>`:"";
    return `<div class="rrow ${cls}"><span class="nm">${F(teamName(s.team))} ${s.name} ${star}${s.aid?`<span class="pclub-i" data-club="${escAttr(s.aid)}"></span>`:""}</span><span class="tags">${tags}</span><span class="rbar"><i style="width:${s.rating*10}%"></i></span><span class="rv">${s.rating.toFixed(1)}</span></div>`;
   }).join("")+`</div>` : `<div class="locked">Ratings appear once goals are scored.</div>`;
 }

 // ---- formations / cards / subs (only with lineup data) ----
 let extraHTML="", teamPerfHTML="", statLeadersHTML="";
 if(lu && (lu.home||lu.away)){
  const pchip=p=>`<span class="pchip"><span class="phead" data-pl="${escAttr(p.name||"")}"><span class="pnum">${p.num||""}</span></span><span class="pnm">${p.name||""}</span>${p.aid?`<span class="pclub" data-club="${escAttr(p.aid)}"></span>`:""}</span>`;
  const pitch=t=>{const b=lu[t]; if(!b||!b.xi||!b.xi.length)return"";
    const gk=b.xi.filter(p=>posTier(p.posAbbr||p.pos)===0);
    const out=b.xi.filter(p=>posTier(p.posAbbr||p.pos)!==0);
    const rowSizes=(b.formation||"").split("-").map(n=>parseInt(n,10)).filter(n=>n>0);
    let rows=[];
    if(rowSizes.length && rowSizes.reduce((a,c)=>a+c,0)===out.length){   // lay out by the real formation
      const sorted=out.slice().sort((a,b)=>posTier(a.posAbbr||a.pos)-posTier(b.posAbbr||b.pos)||(a.fp||0)-(b.fp||0));
      let i=0; rowSizes.forEach(n=>{ const row=sorted.slice(i,i+n); i+=n;
        row.sort((a,b)=>posSide(a.posAbbr)-posSide(b.posAbbr)||(a.fp||0)-(b.fp||0)); rows.push(row); });
    } else {                                                              // no/mismatched formation → bucket by G/D/M/F
      const buck={D:[],M:[],F:[]}; out.forEach(p=>{const k=(p.pos||"M").toUpperCase(); (buck[k]||buck.M).push(p);});
      ["D","M","F"].forEach(k=>{ if(buck[k].length){ buck[k].sort((a,b)=>posSide(a.posAbbr)-posSide(b.posAbbr)); rows.push(buck[k]); } });
    }
    const allRows=[gk].concat(rows).filter(r=>r.length);                 // GK back row, forwards in front
    return `<div class="luhdr"><b>${F(teamName(t))} ${teamName(t)}</b><span class="formtag">${b.formation||""}</span></div>`+
      `<div class="pitch">`+allRows.map(row=>`<div class="pline">`+row.map(pchip).join("")+`</div>`).join("")+`</div>`;
  };
  const cards=(lu.events||[]).filter(e=>e.type==="card").sort((a,b)=>a.min-b.min);
  const subs=(lu.events||[]).filter(e=>e.type==="subst").sort((a,b)=>a.min-b.min);
  const cardsHTML=cards.length?`<div class="cards">`+cards.map(e=>`<div class="cardr"><span class="mn">${e.min}'</span><span class="cardchip ${e.card==="red"?"r":"y"}"></span><span class="nm">${F(teamName(e.team))} ${e.player||""}</span></div>`).join("")+`</div>`:`<div class="locked">No cards.</div>`;
  const subsHTML=subs.length?`<div class="subsl">`+subs.map(e=>`<div class="subr"><span class="mn">${e.min}'</span><span class="in">▲ ${e.assist||"?"}</span><span class="ar">←</span><span class="out">▼ ${e.player||"?"}</span><span class="nm" style="color:var(--mut);font-size:11px">${F(teamName(e.team))}</span></div>`).join("")+`</div>`:`<div class="locked">No substitutions.</div>`;
  const srcLabel = {espn:"Lineups, stats, cards &amp; subs via ESPN", wikipedia:"Lineups, cards &amp; subs via Wikipedia (CC BY-SA)", "api-football":"Lineups via API-Football", "football-data":"Lineups via football-data.org"}[lu.source] || "";
  const attr = `<div class="heatcap">${srcLabel?srcLabel+" · ":""}Player photos via Wikipedia, Wikidata &amp; Wikimedia Commons</div>`;

  // ---- team match stats: side-by-side comparison bars (hide if absent) ----
  let teamStatsHTML="";
  const tsd=lu.teamstats;
  if(tsd && tsd.labels){
   const num=v=>{const x=parseFloat(String(v).replace(/[^0-9.\-]/g,"")); return isNaN(x)?0:x;};
   const rows=Object.keys(tsd.labels).filter(k=>(tsd.home&&k in tsd.home)&&(tsd.away&&k in tsd.away)).map(k=>{
     const hv=tsd.home[k], av=tsd.away[k], isPct=!!(tsd.pct&&tsd.pct[k]);
     const hn=num(hv), an=num(av), tot=hn+an;
     const hp=tot>0?100*hn/tot:50;
     const hd=isPct?hv+"%":hv, ad=isPct?av+"%":av;
     const hL=hn>an, aL=an>hn;
     return `<div class="tsrow"><span class="tsv h ${hL?'lead':''}">${hd}</span><span class="tslbl">${tsd.labels[k]}</span><span class="tsv a ${aL?'lead':''}">${ad}</span>
       <span class="tsbar"><i class="h ${hL?'':'lo'}" style="width:${hp.toFixed(1)}%"></i><i class="a ${aL?'':'lo'}" style="width:${(100-hp).toFixed(1)}%"></i></span></div>`;
   }).join("");
   if(rows) teamStatsHTML=`<div class="mcsec"><h4>Team stats <span class="tag">${F(f.home)} ${f.home} v ${F(f.away)} ${f.away}</span></h4><div class="tstat">${rows}</div></div>`;
  }

  // ---- player match stats: per-team table of players with stats (hide if absent) ----
  let playerStatsHTML="";
  const PCOLS=[["G","Goals"],["A","Assists"],["SH","Shots"],["SOT","On Target"],["FC","Fouls"],["OFF","Offside"],["YC","Yel"],["RC","Red"],["SV","Saves"]];
  const pstatBlock=t=>{const b=lu[t]; if(!b)return"";
    const players=[].concat(b.xi||[],b.subs||[]).filter(p=>p.st);
    if(!players.length)return"";
    const cols=PCOLS.filter(([k])=>players.some(p=>p.st[k]!=null));
    if(!cols.length)return"";
    const colMax={}; cols.forEach(([k])=>{colMax[k]=Math.max(0,...players.map(p=>+p.st[k]||0));});
    const head=`<thead><tr><th class="pn">${F(teamName(t))} ${teamName(t)}</th>`+cols.map(([k,lab])=>`<th title="${lab}">${k}</th>`).join("")+`</tr></thead>`;
    const body=`<tbody>`+players.map(p=>`<tr><td class="pn">${p.name}</td>`+cols.map(([k])=>{const v=p.st[k]; const n=+v||0;
        const hi=(n>0&&n===colMax[k])?" class=\"hi\"":"";
        return `<td${hi}>${(v==null||v===0)?'<span class=z>·</span>':v}</td>`;}).join("")+`</tr>`).join("")+`</tbody>`;
    return `<table class="pstat">${head}${body}</table>`;
  };
  const pst=pstatBlock("home")+pstatBlock("away");
  if(pst) playerStatsHTML=`<div class="mcsec"><h4>Player stats <span class="tag">per match</span></h4>${pst}</div>`;

  // ---- team performance index: composite attack / control / discipline (0–10) ----
  if(tsd && (tsd.home||tsd.away)){
   const N=v=>{const x=parseFloat(String(v).replace(/[^0-9.\-]/g,""));return isNaN(x)?0:x;};
   const gh=score[0], ga=score[1];
   const c10=x=>Math.max(0,Math.min(10,x));                     // clamp to 0–10
   const idx=(d,gf)=>{
     const poss=N(d.possessionPct), sh=N(d.totalShots), sot=N(d.shotsOnTarget),
       pass=N(d.totalPasses), foul=N(d.foulsCommitted), yc=N(d.yellowCards), rc=N(d.redCards);
     const attack     = c10(gf*2.2 + sot*0.55 + sh*0.12);       // finishing + threat
     const control    = c10(poss*0.09 + Math.min(pass,700)*0.004); // possession + circulation
     const discipline = c10(10 - foul*0.25 - yc*1.0 - rc*3.0);  // start clean, deduct
     return {attack, control, discipline};
   };
   const H=idx(tsd.home||{},gh), A=idx(tsd.away||{},ga);
   // every dimension is now a positive 0–10 score → simple head-to-head share for the bars
   const share=(h,a)=>{const t=h+a;return t>0?100*h/t:50;};
   const dims=[["Attack",H.attack,A.attack],["Control",H.control,A.control],["Discipline",H.discipline,A.discipline]];
   const overall=o=>c10(0.45*o.attack + 0.30*o.control + 0.25*o.discipline);
   const oH=overall(H), oA=overall(A);
   const bars=dims.map(([lab,h,a])=>{const hp=share(h,a);const hL=h>a,aL=a>h;
     return `<div class="tsrow"><span class="tsv h ${hL?'lead':''}">${h.toFixed(1)}</span><span class="tslbl">${lab}</span><span class="tsv a ${aL?'lead':''}">${a.toFixed(1)}</span>
       <span class="tsbar"><i class="h ${hL?'':'lo'}" style="width:${hp.toFixed(1)}%"></i><i class="a ${aL?'':'lo'}" style="width:${(100-hp).toFixed(1)}%"></i></span></div>`;}).join("");
   teamPerfHTML=`<div class="mcsec"><h4>Team performance index <span class="tag">our composite · 0–10</span></h4>
     <div class="tpiov"><span class="tpi h">${F(f.home)} ${f.home} <b>${oH.toFixed(1)}</b></span><span class="tpi a"><b>${oA.toFixed(1)}</b> ${f.away} ${F(f.away)}</span></div>
     <div class="tstat">${bars}</div>
     <div class="heatcap">Each scored 0–10 · Attack = goals, shots on target, volume · Control = possession + passing · Discipline = fewer fouls &amp; cards</div></div>`;
  }

  // ---- stat leaders: standout per category across both XIs ----
  const allP=["home","away"].flatMap(t=>[].concat(lu[t]&&lu[t].xi||[],lu[t]&&lu[t].subs||[]).filter(p=>p.st).map(p=>({...p,team:t})));
  if(allP.length){
   const lead=(key,lab,icon)=>{let best=null;allP.forEach(p=>{const v=+p.st[key]||0; if(v>0&&(!best||v>best.v))best={name:p.name,team:p.team,v};});
     return best?`<div class="slchip"><span class="slk">${icon} ${lab}</span><span class="slv"><b>${best.v}</b> ${best.name}</span><span class="slt">${F(teamName(best.team))} ${teamName(best.team)}</span></div>`:"";};
   const chips=[lead("G","Goals","⚽"),lead("SH","Shots","🎯"),lead("SOT","On target","✓"),lead("SV","Saves","🧤"),lead("FS","Fouls won","🛡"),lead("FC","Fouls","⚠")].filter(Boolean).join("");
   if(chips) statLeadersHTML=`<div class="mcsec"><h4>Match stat leaders</h4><div class="sleaders">${chips}</div></div>`;
  }

  extraHTML=`
   <div class="mcsec"><h4>Formations <span class="tag">${(lu.home&&lu.home.formation)||""} v ${(lu.away&&lu.away.formation)||""}</span></h4>${pitch("home")}${pitch("away")}${attr}</div><div id="pedibar"></div>
   ${teamStatsHTML}
   ${teamPerfHTML}
   ${playerStatsHTML}
   <div class="mcsec"><h4>Cards</h4>${cardsHTML}</div>
   <div class="mcsec"><h4>Substitutions</h4>${subsHTML}</div>`;
 } else {
  extraHTML="";   // no lineup data → no formations/cards/subs section (removed by request)
 }

 // ---- result vs model ----
 const pre=WCInPlay.probs(f.eh,f.ea,0,0,0);
 const favIdx=pre.indexOf(Math.max(...pre));
 const favName=favIdx===1?"Draw":favIdx===0?f.home:f.away;
 const actIdx=score[0]>score[1]?0:score[0]<score[1]?2:1;
 const settled=WP.status==="ft", matched=actIdx===favIdx;
 const mvmHTML=`<div class="mvm">
   <div class="box"><div class="k">Model favoured</div><div class="v">${favName} · ${pc(pre[favIdx],0)}</div></div>
   <div class="box"><div class="k">Model xG → actual</div><div class="v">${f.eh.toFixed(2)}–${f.ea.toFixed(2)} → ${score[0]}–${score[1]}</div></div>
   <div class="box"><div class="k">Pre-match odds</div><div class="v" style="font-size:13px">${pc(pre[0],0)} / ${pc(pre[1],0)} / ${pc(pre[2],0)}</div></div>
   <div class="box"><div class="k">${settled?"Outcome":"So far"}</div><div class="v ${settled?(matched?"ok":"no"):""}">${settled?(matched?"✓ as predicted":"✗ upset"):"in progress"}</div></div>
  </div>`;

 // ---- Model vs Market (betting market implied odds vs our model) ----
 let mktSec=""; const mkt=lu&&lu.market;
 if(mkt){ const settled=WP.status==="ft";   // compare like-for-like: PRE-MATCH model (pre) vs the pre-match market line
   const mr=(lab,m,k,idx)=>{const sh=(m+k)>0?100*m/(m+k):50; const md=m-k; const dt=Math.abs(md)>=0.04?` <span class="mv ${md>0?'up':'dn'}">${md>0?'+':''}${pc(md,0)}</span>`:'';
     const isRes=settled&&idx===actIdx;
     const call=isRes?(Math.abs(m-k)<0.02?'<span class="callt">level</span>':m>k?'<span class="callt ok">✓ our model</span>':'<span class="callt mkt">✓ market</span>'):'';
     return `<div class="tsrow${isRes?' resrow':''}"><span class="tsv h ${m>=k?'lead':''}">${pc(m,0)}</span><span class="tslbl">${lab}${dt}${call}</span><span class="tsv a ${k>m?'lead':''}">${pc(k,0)}</span><span class="tsbar"><i class="h ${m>=k?'':'lo'}" style="width:${sh.toFixed(0)}%"></i><i class="a ${k>m?'':'lo'}" style="width:${(100-sh).toFixed(0)}%"></i></span></div>`;};
   mktSec=`<div class="mcsec"><h4>Model vs Market <span class="tag">pre-match · our model v ${mkt.prov}</span></h4>
     <div class="tpiov"><span class="tpi h">Our model</span><span class="tpi a">Market</span></div>
     <div class="tstat">${mr(F(f.home)+" "+f.home+" win",pre[0],mkt.h,0)}${mr("Draw",pre[1],mkt.d,1)}${mr(F(f.away)+" "+f.away+" win",pre[2],mkt.a,2)}</div>
     <div class="heatcap">${settled?`Pre-match forecasts vs the actual result (${score[0]}–${score[1]}).`:"Pre-match forecasts — what each gave before kickoff. The market line isn't updated live."}</div></div>`;
 }

 // ---- live qualification impact of the current scoreline ----
 let impSec=""; const cond=LAST&&LAST.cond;
 if(WP.status==="live" && cond){ const base=D.baseline||{};
   const outcome=side=>{ if(score[0]===score[1])return "draw"; const hw=score[0]>score[1]; return side==="home"?(hw?"win":"lose"):(hw?"lose":"win"); };
   const imp=(team,side)=>{ const c=cond[team], o=outcome(side); if(!c||!c[o]||c[o].p==null)return "";
     const p=c[o].p, b=base[team]&&base[team].p_reach_r32, d=b!=null?p-b:0;
     const arr=d>0.012?`<span class="mv up">▲ ${pc(d,0)}</span>`:d<-0.012?`<span class="mv dn">▼ ${pc(-d,0)}</span>`:`<span class="mv fl">–</span>`;
     return `<div class="scenrow"><span class="gb">${F(team)}</span><span class="snm">${team}</span><span class="stag hunt">${pc(p,0)} to advance</span>${arr}</div>`;};
   const hi=imp(f.home,"home"), ai=imp(f.away,"away");
   if(hi||ai) impSec=`<div class="mcsec"><h4>If it ends ${score[0]}–${score[1]} <span class="tag">live qualification impact · Δ vs pre-tournament</span></h4>${hi}${ai}</div>`;
 }

 // ---- live commentary / play-by-play ----
 let commSec=""; const comm=(lu&&lu.commentary)||[];
 if(comm.length){ const ic={goal:"⚽",og:"⚽",pen:"🎯",yellow:"🟨",red:"🟥",sub:"🔁",save:"🧤",miss:"↗️",corner:"⛳",offside:"🚩",foul:"⚠️",whistle:"🔔"};
   const rows=comm.slice().reverse().slice(0,40).map(c=>{ const mn=c.min!=null?(c.min+(c.add?"+"+c.add:"")+"'"):"";
     return `<div class="commrow ${(c.type==='goal'||c.type==='og'||c.type==='red')?'big':''}"><span class="cmn">${mn}</span><span class="cic">${ic[c.type]||"·"}</span><span class="ctx">${c.text}</span></div>`;}).join("");
   commSec=`<div class="mcsec"><h4>Commentary <span class="tag">live play-by-play</span></h4><div class="commlist">${rows}</div></div>`;
 }

 return `<div class="mc">
   ${mktSec}
   ${impSec}
   ${commSec}
   ${statLeadersHTML}
   <div class="mcsec"><h4>Our player ratings <span class="tag">${ratTag}</span></h4>${ratHTML}</div>
   <div class="mcsec"><h4>Goals</h4>${golHTML}</div>
   ${heatHTML}
   ${extraHTML}
   <div class="mcsec"><h4>Result vs model</h4>${mvmHTML}</div>
  </div>`;
}
function drawModal(){
 const f=fixById[WP.fid];
 const kt=f.utc?new Date(f.utc):null;

 // --- not yet kicked off: pre-match odds only, no fabricated timeline ---
 if(WP.status==="upcoming"){
  const pre=WCInPlay.probs(f.eh,f.ea,0,0,0);
  modalEl.innerHTML=`
   <button class="close" id="wpclose" aria-label="Close match centre">✕</button>
   <div class="mh"><span class="tn">${F(f.home)} ${f.home}</span><span class="sc" style="font-size:22px;color:var(--mut)">vs</span><span class="tn">${f.away} ${F(f.away)}</span></div>
   <div class="meta">Group ${f.group} · ${f.city}${kt?" · "+fmtDay.format(kt)+", "+fmtTime.format(kt):""} · model xG ${f.eh.toFixed(2)}–${f.ea.toFixed(2)}</div>
   ${readouts(f,pre)}
   <div class="hint" style="margin-top:18px">Pre-match model odds shown above. The live win-probability timeline appears once the match kicks off${kt?` at ${fmtTime.format(kt)} your time`:""}.</div>`;
  document.getElementById("wpclose").onclick=closeModal;
  return;
 }

 // --- live or finished: real in-play win-probability chart ---
 const T=WCInPlay.timeline(f.eh,f.ea,WP.events,WP.full,WP.reds);
 const [gh,ga]=WCInPlay.scoreAt(WP.events,WP.minute);
 // current readout: for a live match, also reflect red cards + shot dominance at this minute
 let cur=T[WP.minute].p;
 if(WP.status==="live"){ const rc=WCInPlay.redsAt(WP.reds,WP.minute), sh=sotOf(f);
   cur=WCInPlay.probs(f.eh,f.ea,gh,ga,WP.minute,WP.full,Object.assign({},rc,sh||{})); }
 const mlbl=m=>m>90?"90+"+(m-90):(""+m);
 const statusTxt = WP.status==="live" ? `● LIVE — ${mlbl(WP.minute)}′` : "Full time · actual goal timeline";
 const liveNote = (WP.status==="live" && WP.events.length===0)
   ? `<div class="hint" style="margin-top:8px">No goals reported yet — showing the live win probability at the current scoreline. The full goal-by-goal timeline fills in as the match progresses.</div>` : "";
 const redNote = (WP.reds&&WP.reds.length)
   ? `<div class="hint" style="margin-top:6px">🟥 Model adjusts for the red card${WP.reds.length>1?"s":""}: ${WP.reds.map(r=>(F(r.team==="home"?f.home:f.away)+" "+(r.team==="home"?f.home:f.away)+" "+r.min+"′")).join(", ")} — a side down to ten scores less and concedes more${WP.status==="live"&&sotOf(f)?", and the live readout reflects shot dominance":""}.</div>` : "";
 modalEl.innerHTML=`
  <button class="close" id="wpclose" aria-label="Close match centre">✕</button>
  <div class="mh"><span class="tn">${F(f.home)} ${f.home}</span><span class="sc">${gh} – ${ga}</span><span class="tn">${f.away} ${F(f.away)}</span></div>
  <div class="meta">Group ${f.group} · ${f.city}${kt?" · "+fmtDay.format(kt):""} · model xG ${f.eh.toFixed(2)}–${f.ea.toFixed(2)} · <b style="color:${WP.status==="live"?"var(--live)":"var(--blue)"}">${statusTxt}</b></div>
  ${readouts(f,cur)}
  <div class="chartbox">${buildChart(f)}</div>
  <div class="minrow"><span class="mm">${mlbl(WP.minute)}'</span>
   <input type="range" id="wpmin" min="0" max="${WP.full||90}" value="${WP.minute}"></div>
  <div class="ctrls">
   <div class="seg"><button class="solid" id="wpplay">▶ Replay</button><button id="wprewind" aria-label="Restart from kickoff">↺</button></div>
  </div>
  ${liveNote}${redNote}
  <div class="hint">Remaining-time goals modelled as Poisson(xG × time left) — exact in-play win probability from the real scoreline. Drag to scrub the minute, or press Replay.</div>
  ${matchCentre(f)}`;
 document.getElementById("wpclose").onclick=closeModal;
 const mr=document.getElementById("wpmin");
 mr.oninput=()=>{WP.minute=+mr.value;WP.followLive=false;stopAnim();drawModal();};
 document.getElementById("wpplay").onclick=animateToggle;
 document.getElementById("wprewind").onclick=()=>{WP.minute=0;WP.followLive=false;stopAnim();drawModal();};
 hydratePhotos(modalEl);   // fill in player headshots (Wikipedia, cached) after the pitch renders
 hydrateClubs(modalEl);    // fill in each player's current club (ESPN athlete endpoint, cached)
 { const _lu=f&&D.lineups[f.home+"|"+f.away]; if(_lu) hydratePedigree(modalEl, _lu); }   // squad pedigree (display only)
}
let animTimer=null;
function stopAnim(){if(animTimer){clearInterval(animTimer);animTimer=null;const b=document.getElementById("wpplay");if(b)b.textContent="▶ Play";}}
function animateToggle(){ if(animTimer){stopAnim();return;} animatePlay(); }
function animatePlay(){ stopAnim(); WP.followLive=false; const FM=WP.full||90; if(WP.minute>=FM)WP.minute=0; const b=document.getElementById("wpplay");if(b)b.textContent="⏸ Pause";
 animTimer=setInterval(()=>{ WP.minute+=1; if(WP.minute>=FM){WP.minute=FM;drawModal();stopAnim();return;} drawModal(); },55); }

document.getElementById("feedbox").addEventListener("click",e=>{const c=e.target.closest(".mcard.clk");if(c)openMatch(+c.dataset.fid);});
document.getElementById("tickerbar").addEventListener("click",e=>{const c=e.target.closest(".tk.clk");if(c)openMatch(+c.dataset.fid);});
document.getElementById("oddstable").addEventListener("click",e=>{const tr=e.target.closest("tr[data-team]");if(tr)openTeam(tr.dataset.team);});
addEventListener("keydown",e=>{if(e.key==="Escape")closeTeam();});

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
