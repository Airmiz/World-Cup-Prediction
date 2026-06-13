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
.pline{display:flex;justify-content:center;gap:8px;flex-wrap:wrap}
.pchip{font-size:11px;background:var(--surface);box-shadow:var(--shadow);border-radius:8px;padding:4px 9px;display:flex;align-items:center;gap:5px;max-width:130px}
.pchip .n{font-weight:700;color:var(--mut);font-size:10px}
.pchip .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
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
</style>
</head>
<body>
<nav><div class="in"><b><span class="lg">26</span> World Cup 26</b>
<a href="index.html">Forecast</a><a href="#feed" class="on">Live</a><a href="#stats">Stats</a><a href="#tracker">Title race</a><a href="#groups">Groups</a><a href="#odds">Title odds</a><a href="#bracket">Bracket</a></div></nav>
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

<section id="stats">
 <div class="shead"><h2>Tournament stats</h2><p>Live leaderboards and model-driven storylines, built from real match data — the Golden Boot race, our own player power rankings, and how the tournament is defying (or matching) the forecast.</p></div>
 <div id="statsbox"></div>
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
  renderStatus(); renderBig(out); renderFeed(); renderStats(); renderTracker(); renderGroups(out); renderOdds(out); renderBracket(out);
 },20);
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
 const scorers={}, ratingAcc={}, teamAcc={};
 let totalGoals=0;
 keys.forEach(k=>{
   const ev=D.goal_events[k], f=fxKey[k], score=matchScore(f,ev);
   totalGoals+=score[0]+score[1];
   ev.forEach(e=>{ if(e.og)return; const t=e.team==="home"?f.home:f.away; const id=e.name+"|"+t;
     const s=scorers[id]||(scorers[id]={name:e.name,team:t,goals:0,pens:0}); s.goals++; if(e.pen)s.pens++; });
   // full-model ratings when a lineup exists for this match; else goal-contributor fallback
   const lu=D.lineups[k];
   const rated = (lu && (lu.home||lu.away)) ? fullSquadRatings(lu,score) : playerRatings(ev,score);
   rated.forEach(r=>{ const t=r.team==="home"?f.home:f.away; const id=r.name+"|"+t;
     const a=ratingAcc[id]||(ratingAcc[id]={name:r.name,team:t,pos:r.pos||"",sum:0,n:0,best:0,goals:0,assists:0});
     a.sum+=r.rating; a.n++; a.best=Math.max(a.best,r.rating); a.goals+=r.goals||0; a.assists+=r.assists||0;
     const ta=teamAcc[t]||(teamAcc[t]={team:t,sum:0,n:0}); ta.sum+=r.rating; ta.n++;
   });
 });
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
   const tl=WCInPlay.timeline(f.eh,f.ea,ev); let mx=0,mn=1; tl.forEach(p=>{mx=Math.max(mx,p.p[0]);mn=Math.min(mn,p.p[0]);});
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

 box.innerHTML=`
  <div class="stwrap">
   <div class="stcard"><h3>🥇 Golden Boot</h3>${bootHTML}</div>
   <div class="stcard"><h3>⭐ Top performers <span style="font-size:9.5px;color:var(--blue);background:var(--blue-soft);border-radius:6px;padding:2px 7px">avg rating · model v2</span></h3>${powerHTML}</div>
   <div class="stcard"><h3>🛡 Team rating table <span style="font-size:9.5px;color:var(--blue);background:var(--blue-soft);border-radius:6px;padding:2px 7px">squad avg</span></h3>${teamRankHTML}</div>
  </div>
  <div class="stcard" style="margin-top:16px"><h3>📈 Storylines</h3><div class="tiles">${tiles}</div></div>`;
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
 autoTimer=setTimeout(()=>{loadLive().then(scheduleAuto);},90000); }

document.getElementById("ftN").textContent=NSIMS.toLocaleString();
loadLive().then(scheduleAuto);

/* ===== Win-probability explorer ===== */
const WP={fid:null,events:[],minute:90,anim:null,mode:"actual"};
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
  <button class="close" id="tmclose">✕</button>
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
 const t=f.utc?new Date(f.utc).getTime():null;
 if(t && Date.now()>=t) return "live";
 return "upcoming";
}
function openMatch(fid){
 const f=fixById[fid]; if(!f) return;
 WP.fid=fid; stopAnim();
 const res=STATE.results[fid];
 const known=D.goal_events[f.home+"|"+f.away];
 WP.status=matchStatus(fid);
 if(WP.status==="ft"){
   WP.events = known ? known.map(e=>({...e})) : (res ? spreadGoals(res[0],res[1]) : []);
   WP.minute = 90;
 } else if(WP.status==="live"){
   WP.events = known ? known.map(e=>({...e})) : [];   // real goals if available, else 0-0 baseline
   const t=new Date(f.utc).getTime();
   WP.minute = Math.max(0, Math.min(90, Math.round((Date.now()-t)/60000)));
 } else {
   WP.events=[]; WP.minute=0;                          // upcoming: no fabricated story
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
  shot:0.05, shotCap:0.40, sot:0.11, sotCap:0.55,
  og:-1.60, miss:-0.70, foulC:-0.06, foulCcap:-0.40, foulS:0.03, foulScap:0.25,
  offside:-0.05, offCap:-0.25, yel:-0.30, red:-1.20,
  save:0.18, saveCap:1.20, gkConcede:-0.22, cleanGK:0.70, cleanDef:0.45, defConcede:-0.18,
  winStart:0.25, drawStart:0.05 };
const clampR=x=>Math.max(3,Math.min(10,Math.round(x*10)/10));
function togRate(el){const d=el.nextElementSibling; if(d&&d.classList.contains("rdet")){d.classList.toggle("open"); el.classList.toggle("ropen");}}
const cap=(v,lo,hi)=>Math.max(lo===null?-1e9:lo,Math.min(hi===null?1e9:hi,v));

/* Full-squad ratings from a lineup + events + per-player stats (our model v2). */
function fullSquadRatings(lu, score){
 const conceded={home:score[1],away:score[0]};
 const won={home:score[0]>score[1],away:score[1]>score[0]}, drew=score[0]===score[1];
 const stat={};
 const ensure=(t,name,pos,num,started)=>{const k=t+"|"+name; return stat[k]||(stat[k]={team:t,name,pos:(pos||"").toUpperCase(),num:num,goals:0,pens:0,assists:0,og:0,yel:0,red:0,missed:0,on:false,off:false,started,st:null});};
 ["home","away"].forEach(t=>{const b=lu[t]; if(!b)return;
   (b.xi||[]).forEach(p=>{const s=ensure(t,p.name,p.pos,p.num,true); if(p.st)s.st=p.st;});
   (b.subs||[]).forEach(p=>{const s=ensure(t,p.name,p.pos,p.num,false); if(p.st)s.st=p.st;});});
 (lu.events||[]).forEach(e=>{
   if(e.type==="goal"){const d=(e.detail||"").toLowerCase();
     const s=findStat(stat,e.player);
     if(d.includes("own")){ if(s)s.og++; }
     else if(d.includes("miss")){ if(s)s.missed++; }
     else { if(s){s.goals++; if(d.includes("pen"))s.pens++;} const a=e.assist&&findStat(stat,e.assist); if(a)a.assists++; }
   } else if(e.type==="card"){const s=findStat(stat,e.player); if(s){e.card==="red"?s.red++:s.yel++;}}
   else if(e.type==="subst"){const onP=e.assist&&findStat(stat,e.assist); const offP=findStat(stat,e.player); if(onP)onP.on=true; if(offP)offP.off=true;}
 });
 return Object.values(stat).filter(s=>s.started||s.on).map(s=>{
   const bd=[]; const base=s.started?6.5:6.4;
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
     add("Fouls committed",cap(RW.foulC*(+st.FC||0),RW.foulCcap,0));
     add("Fouls won",cap(RW.foulS*(+st.FS||0),0,RW.foulScap));
     if(s.pos==="F"||s.pos==="M") add("Offsides",cap(RW.offside*(+st.OFF||0),RW.offCap,0));
   }
   if(s.pos==="G"){
     add("Saves",cap(RW.save*(+st.SV||0),0,RW.saveCap));
     const gc = has && st.GC!=null ? (+st.GC||0) : (s.started?conceded[s.team]:0);
     add("Goals conceded",RW.gkConcede*gc);
     if(s.started&&conceded[s.team]===0) add("Clean sheet",RW.cleanGK);
   } else if(s.pos==="D"){
     if(s.started&&conceded[s.team]===0) add("Clean sheet",RW.cleanDef);
     else if(conceded[s.team]>=2) add("Heavy concession",RW.defConcede*(conceded[s.team]-1));
   }
   if(s.started){ if(won[s.team])add("Team won",RW.winStart); else if(drew)add("Team drew",RW.drawStart); }
   const rating=clampR(base + bd.reduce((a,x)=>a+x.v,0));
   return {team:s.team,name:s.name,pos:s.pos,num:s.num,started:s.started,on:s.on,
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
 const score = (WP.status==="ft" && res) ? res : WCInPlay.scoreAt(ev, WP.status==="live"?WP.minute:90);
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
   return `<div class="gol"><span class="mn">${e.min}'</span><span class="ic">⚽</span><span class="nm">${F(teamName(pt))} ${e.name||"—"}</span>${bdg}</div>`;
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
    if(!s.started&&s.on)o.push(`<span class="tg sub" title="Substitute">SUB</span>`);
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
    return `<div class="rrow ${cls}"><span class="nm">${F(teamName(s.team))} ${s.name} ${star}</span><span class="tags">${tags}</span><span class="rbar"><i style="width:${s.rating*10}%"></i></span><span class="rv">${s.rating.toFixed(1)}</span></div>`;
   }).join("")+`</div>` : `<div class="locked">Ratings appear once goals are scored.</div>`;
 }

 // ---- formations / cards / subs (only with lineup data) ----
 let extraHTML="", teamPerfHTML="", statLeadersHTML="";
 if(lu && (lu.home||lu.away)){
  const posOrder={G:0,D:1,M:2,F:3};
  const pitch=t=>{const b=lu[t]; if(!b||!b.xi||!b.xi.length)return"";
    const lines={G:[],D:[],M:[],F:[]};
    b.xi.forEach(p=>{const k=(p.pos||"M").toUpperCase(); (lines[k]||lines.M).push(p);});
    const rows=["G","D","M","F"].filter(k=>lines[k].length).map(k=>
      `<div class="pline">`+lines[k].map(p=>`<span class="pchip"><span class="n">${p.num||""}</span><span class="nm">${p.name}</span></span>`).join("")+`</div>`).join("");
    return `<div class="luhdr"><b>${F(teamName(t))} ${teamName(t)}</b><span class="formtag">${b.formation||""}</span></div><div class="pitch">${rows}</div>`;
  };
  const cards=(lu.events||[]).filter(e=>e.type==="card").sort((a,b)=>a.min-b.min);
  const subs=(lu.events||[]).filter(e=>e.type==="subst").sort((a,b)=>a.min-b.min);
  const cardsHTML=cards.length?`<div class="cards">`+cards.map(e=>`<div class="cardr"><span class="mn">${e.min}'</span><span class="cardchip ${e.card==="red"?"r":"y"}"></span><span class="nm">${F(teamName(e.team))} ${e.player||""}</span></div>`).join("")+`</div>`:`<div class="locked">No cards.</div>`;
  const subsHTML=subs.length?`<div class="subsl">`+subs.map(e=>`<div class="subr"><span class="mn">${e.min}'</span><span class="in">▲ ${e.assist||"?"}</span><span class="ar">←</span><span class="out">▼ ${e.player||"?"}</span><span class="nm" style="color:var(--mut);font-size:11px">${F(teamName(e.team))}</span></div>`).join("")+`</div>`:`<div class="locked">No substitutions.</div>`;
  const srcLabel = {espn:"Lineups, stats, cards &amp; subs via ESPN", wikipedia:"Lineups, cards &amp; subs via Wikipedia (CC BY-SA)", "api-football":"Lineups via API-Football", "football-data":"Lineups via football-data.org"}[lu.source] || "";
  const attr = srcLabel ? `<div class="heatcap">${srcLabel}</div>` : "";

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
   const idx=(d,gf,ga2)=>{
     const poss=N(d.possessionPct), sh=N(d.totalShots), sot=N(d.shotsOnTarget),
       pass=N(d.totalPasses), foul=N(d.foulsCommitted), yc=N(d.yellowCards), rc=N(d.redCards);
     const attack = 2.0*gf + 0.9*sot + 0.18*sh;                 // finishing + threat
     const control = 0.045*poss + 0.0035*pass;                  // possession + circulation
     const discipline = -0.12*foul - 0.6*yc - 1.6*rc;           // fewer fouls/cards = better
     return {attack, control, discipline};
   };
   const H=idx(tsd.home||{},gh,ga), A=idx(tsd.away||{},ga,gh);
   // scale each dimension to a 0–100 share between the two sides for the bars
   const share=(h,a)=>{const lo=Math.min(h,a,0);const H2=h-lo,A2=a-lo,t=H2+A2;return t>0?100*H2/t:50;};
   const dims=[["Attack",H.attack,A.attack],["Control",H.control,A.control],["Discipline",H.discipline,A.discipline]];
   const overall=t=>{const o=t==="h"?H:A; return Math.max(0,Math.min(10, 5 + 0.55*(o.attack) + 0.4*(o.control-3.4) + 0.5*o.discipline ));};
   const oH=overall("h"), oA=overall("a");
   const bars=dims.map(([lab,h,a])=>{const hp=share(h,a);const hL=h>a,aL=a>h;
     return `<div class="tsrow"><span class="tsv h ${hL?'lead':''}">${h.toFixed(1)}</span><span class="tslbl">${lab}</span><span class="tsv a ${aL?'lead':''}">${a.toFixed(1)}</span>
       <span class="tsbar"><i class="h ${hL?'':'lo'}" style="width:${hp.toFixed(1)}%"></i><i class="a ${aL?'':'lo'}" style="width:${(100-hp).toFixed(1)}%"></i></span></div>`;}).join("");
   teamPerfHTML=`<div class="mcsec"><h4>Team performance index <span class="tag">our composite · 0–10</span></h4>
     <div class="tpiov"><span class="tpi h">${F(f.home)} ${f.home} <b>${oH.toFixed(1)}</b></span><span class="tpi a"><b>${oA.toFixed(1)}</b> ${f.away} ${F(f.away)}</span></div>
     <div class="tstat">${bars}</div>
     <div class="heatcap">Attack = goals + shots on target + shot volume · Control = possession + passing · Discipline = fouls &amp; cards (higher is cleaner)</div></div>`;
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
   <div class="mcsec"><h4>Formations <span class="tag">${(lu.home&&lu.home.formation)||""} v ${(lu.away&&lu.away.formation)||""}</span></h4>${pitch("home")}${pitch("away")}${attr}</div>
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

 return `<div class="mc">
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
   <button class="close" id="wpclose">✕</button>
   <div class="mh"><span class="tn">${F(f.home)} ${f.home}</span><span class="sc" style="font-size:22px;color:var(--mut)">vs</span><span class="tn">${f.away} ${F(f.away)}</span></div>
   <div class="meta">Group ${f.group} · ${f.city}${kt?" · "+fmtDay.format(kt)+", "+fmtTime.format(kt):""} · model xG ${f.eh.toFixed(2)}–${f.ea.toFixed(2)}</div>
   ${readouts(f,pre)}
   <div class="hint" style="margin-top:18px">Pre-match model odds shown above. The live win-probability timeline appears once the match kicks off${kt?` at ${fmtTime.format(kt)} your time`:""}.</div>`;
  document.getElementById("wpclose").onclick=closeModal;
  return;
 }

 // --- live or finished: real in-play win-probability chart ---
 const T=WCInPlay.timeline(f.eh,f.ea,WP.events);
 const [gh,ga]=WCInPlay.scoreAt(WP.events,WP.minute);
 const cur=T[WP.minute].p;
 const statusTxt = WP.status==="live" ? `● LIVE — ${WP.minute}′` : "Full time · actual goal timeline";
 const liveNote = (WP.status==="live" && WP.events.length===0)
   ? `<div class="hint" style="margin-top:8px">No goals reported yet — showing the live win probability at the current scoreline. The full goal-by-goal timeline fills in as the match progresses.</div>` : "";
 modalEl.innerHTML=`
  <button class="close" id="wpclose">✕</button>
  <div class="mh"><span class="tn">${F(f.home)} ${f.home}</span><span class="sc">${gh} – ${ga}</span><span class="tn">${f.away} ${F(f.away)}</span></div>
  <div class="meta">Group ${f.group} · ${f.city}${kt?" · "+fmtDay.format(kt):""} · model xG ${f.eh.toFixed(2)}–${f.ea.toFixed(2)} · <b style="color:${WP.status==="live"?"var(--live)":"var(--blue)"}">${statusTxt}</b></div>
  ${readouts(f,cur)}
  <div class="chartbox">${buildChart(f)}</div>
  <div class="minrow"><span class="mm">${WP.minute}'</span>
   <input type="range" id="wpmin" min="0" max="90" value="${WP.minute}"></div>
  <div class="ctrls">
   <div class="seg"><button class="solid" id="wpplay">▶ Replay</button><button id="wprewind">↺</button></div>
  </div>
  ${liveNote}
  <div class="hint">Remaining-time goals modelled as Poisson(xG × time left) — exact in-play win probability from the real scoreline. Drag to scrub the minute, or press Replay.</div>
  ${matchCentre(f)}`;
 document.getElementById("wpclose").onclick=closeModal;
 const mr=document.getElementById("wpmin");
 mr.oninput=()=>{WP.minute=+mr.value;stopAnim();drawModal();};
 document.getElementById("wpplay").onclick=animateToggle;
 document.getElementById("wprewind").onclick=()=>{WP.minute=0;stopAnim();drawModal();};
}
let animTimer=null;
function stopAnim(){if(animTimer){clearInterval(animTimer);animTimer=null;const b=document.getElementById("wpplay");if(b)b.textContent="▶ Play";}}
function animateToggle(){ if(animTimer){stopAnim();return;} animatePlay(); }
function animatePlay(){ stopAnim(); if(WP.minute>=90)WP.minute=0; const b=document.getElementById("wpplay");if(b)b.textContent="⏸ Pause";
 animTimer=setInterval(()=>{ WP.minute+=1; if(WP.minute>=90){WP.minute=90;drawModal();stopAnim();return;} drawModal(); },55); }

document.getElementById("feedbox").addEventListener("click",e=>{const c=e.target.closest(".mcard.clk");if(c)openMatch(+c.dataset.fid);});
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
