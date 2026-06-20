/* World Cup 2026 — in-browser live Monte Carlo engine.
 * Pure functions (no DOM), usable in Node for tests and in the browser.
 * Conditions on real results already played; samples the rest from the
 * model's embedded per-fixture score PMFs and 48x48 knockout win matrices.
 */
(function (root) {
"use strict";

function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}

function buildIndex(D){
  const idx={}; D.teams.forEach((t,i)=>idx[t]=i);
  const groupOf={}; for(const g of D.group_order) for(const t of D.groups[g]) groupOf[t]=g;
  // group fixtures grouped by group letter, with local team positions
  const gfix={}; for(const g of D.group_order) gfix[g]=[];
  D.fixtures.forEach(f=>{ const g=f.group;
    gfix[g].push({id:f.id, hi:D.groups[g].indexOf(f.home), ai:D.groups[g].indexOf(f.away),
                  home:f.home, away:f.away}); });
  // CDF per fixture for fast sampling
  const cdf=D.fixtures.map(f=>{const c=f.pmf.slice();for(let i=1;i<c.length;i++)c[i]+=c[i-1];c[c.length-1]=1;return c;});
  return {idx,groupOf,gfix,cdf};
}

function sampleScore(cdf,G,r){ const x=r(); let lo=0,hi=cdf.length-1;
  while(lo<hi){const m=(lo+hi)>>1; if(cdf[m]<x)lo=m+1; else hi=m;} return [Math.floor(lo/G), lo%G]; }

/* Resolve one knockout tie -> winner global index. */
function koWin(D, i1, i2, venueCountry, r, played){
  if(played!=null) return played;
  const hosts=D.hosts, t1=D.teams[i1], t2=D.teams[i2];
  let p;
  if(hosts.includes(t1) && t1===venueCountry) p=D.P1[i1][i2];
  else if(hosts.includes(t2) && t2===venueCountry) p=1-D.P1[i2][i1];
  else p=D.P0[i1][i2];
  return r()<p ? i1 : i2;
}

/* 2026 FIFA group tiebreakers (NEW for this tournament): when teams are level on points,
 * HEAD-TO-HEAD comes first (h2h points, then h2h goal diff, then h2h goals among the tied
 * teams), and only after that overall goal difference, overall goals, then conduct/ranking
 * (here a random proxy). pgf[a+","+b] = goals a scored against b. */
function breakTie(block, pts, gd, gf, pgf, r){
  if(block.length<2) return block;
  const mp={},mg={},mf={}; block.forEach(t=>{mp[t]=0;mg[t]=0;mf[t]=0;});
  for(let i=0;i<block.length;i++) for(let j=i+1;j<block.length;j++){ const a=block[i],b=block[j];
    const ga=pgf[a+","+b], gb=pgf[b+","+a]; if(ga==null||gb==null) continue;   // not played yet (partial table)
    mf[a]+=ga; mf[b]+=gb; mg[a]+=ga-gb; mg[b]+=gb-ga;
    if(ga>gb)mp[a]+=3; else if(gb>ga)mp[b]+=3; else {mp[a]++;mp[b]++;} }
  const sorted=block.slice().sort((a,b)=>(mp[b]-mp[a])||(mg[b]-mg[a])||(mf[b]-mf[a])||(gd[b]-gd[a])||(gf[b]-gf[a])||(r()-0.5));
  const res=[]; let i=0;                                  // re-apply h2h to any still-tied SUBSET smaller than the block
  while(i<sorted.length){ let j=i;
    while(j+1<sorted.length && mp[sorted[j+1]]===mp[sorted[i]] && mg[sorted[j+1]]===mg[sorted[i]] && mf[sorted[j+1]]===mf[sorted[i]]) j++;
    const sub=sorted.slice(i,j+1);
    if(sub.length>1 && sub.length<block.length) breakTie(sub,pts,gd,gf,pgf,r).forEach(t=>res.push(t));
    else sub.forEach(t=>res.push(t));
    i=j+1; }
  return res;
}
function rank2026(teams, pts, gd, gf, pgf, r){
  const arr=teams.slice().sort((a,b)=>pts[b]-pts[a]); const out=[]; let i=0;
  while(i<arr.length){ let j=i; while(j+1<arr.length && pts[arr[j+1]]===pts[arr[i]]) j++;
    breakTie(arr.slice(i,j+1), pts, gd, gf, pgf, r).forEach(t=>out.push(t)); i=j+1; }
  return out;
}
/* Group standings for ONE group given scorelines [hs,as] per local fixture.
 * Returns local-index order best->worst, plus pts/gd/gf arrays. */
function standGroup(fixtures, scores, r){
  const pts=[0,0,0,0], gd=[0,0,0,0], gf=[0,0,0,0], pgf={};
  fixtures.forEach((f,k)=>{ const [hs,as]=scores[k]; const x=f.hi,y=f.ai;
    if(hs>as){pts[x]+=3;} else if(hs<as){pts[y]+=3;} else {pts[x]++;pts[y]++;}
    gd[x]+=hs-as; gd[y]+=as-hs; gf[x]+=hs; gf[y]+=as;
    pgf[x+","+y]=(pgf[x+","+y]||0)+hs; pgf[y+","+x]=(pgf[y+","+x]||0)+as; });
  const order=rank2026([0,1,2,3], pts, gd, gf, pgf, r);
  return {order,pts,gd,gf};
}

/* One full-tournament simulation. results: {fixtureId:[hs,as]} actual; ko:{matchNo:winnerName} actual. */
function simOnce(D,P,results,ko,r){
  const {gfix,cdf,idx,groupOf}=P, G=D.grid;
  const winners={}, runners={}, thirds={}, thirdRec={};
  const reach=P._reach;                 // reused typed arrays
  for(const g of D.group_order){
    const fx=gfix[g];
    const sc=fx.map(f=> results[f.id] || sampleScore(cdf[f.id],G,r));
    if(P.condTeams&&P.condTeams.length){ for(let k=0;k<fx.length;k++){ const nt=P.fixNextTeams[fx[k].id];
      if(nt){ const hs=sc[k][0],as=sc[k][1]; for(let j=0;j<nt.length;j++){ const e=nt[j];
        P.nextOutcome[e.idx]= e.isHome?(hs>as?0:hs<as?2:1):(as>hs?0:as<hs?2:1); } } } }
    const {order,pts,gd,gf}=standGroup(fx,sc,r);
    const gt=D.groups[g];
    winners[g]=gt[order[0]]; runners[g]=gt[order[1]]; thirds[g]=gt[order[2]];
    reach.r32[idx[gt[order[0]]]]++; reach.r32[idx[gt[order[1]]]]++;
    P.pos[idx[gt[order[0]]]][0]++; P.pos[idx[gt[order[1]]]][1]++;
    P.pos[idx[gt[order[2]]]][2]++; P.pos[idx[gt[order[3]]]][3]++;
    thirdRec[g]={pts:pts[order[2]],gd:gd[order[2]],gf:gf[order[2]]};
  }
  // best 8 thirds
  const tg=D.group_order.split("");
  tg.sort((a,b)=>{const A=thirdRec[a],B=thirdRec[b];
    return (B.pts-A.pts)||(B.gd-A.gd)||(B.gf-A.gf)|| (r()-0.5);});
  const qualG=tg.slice(0,8).sort();
  qualG.forEach(g=>reach.r32[idx[thirds[g]]]++);
  if(P.condTeams&&P.condTeams.length){ const qs={}; for(let i=0;i<qualG.length;i++)qs[qualG[i]]=1;
    for(let c=0;c<P.condTeams.length;c++){ const ti=P.condTeams[c], name=D.teams[ti], g=groupOf[name];
      const adv=(name===winners[g]||name===runners[g]||(name===thirds[g]&&qs[g])); const o=P.nextOutcome[ti];
      P.condN[ti*3+o]++; if(adv)P.condAdv[ti*3+o]++; } }
  const combo=qualG.join("");
  const slotGroups=D.annex[combo];
  const thirdForSlot={};
  D.third_slots.forEach((s,i)=> thirdForSlot[s]=thirds[slotGroups[i]]);

  // resolve a code -> team name
  const teamOf=(code,info)=> code==="3rd" ? thirdForSlot[info.third_slot]
      : (code[0]==="1"?winners:runners)[code[1]];

  const wmatch={};
  for(const mno in D.ko_struct.r32){ const info=D.ko_struct.r32[mno];
    const t1=teamOf(info.home,info), t2=teamOf(info.away,info);
    let pl=null; if(ko[mno]!=null) pl=idx[ko[mno]];
    wmatch[mno]=koWin(D,idx[t1],idx[t2],info.venue_country,r,pl);
    reach.r16[wmatch[mno]]++;
  }
  const rounds=[["r16","qf"],["qf","sf"],["sf","final"]];
  const reachKey={qf:reach.qf,sf:reach.sf,final:reach.final};
  for(const [rk,nk] of rounds){ const st=D.ko_struct[rk];
    for(const mno in st){ const [m1,m2,venue]=st[mno];
      let pl=null; if(ko[mno]!=null) pl=idx[ko[mno]];
      const wn=koWin(D,wmatch[m1],wmatch[m2],venue,r,pl);
      wmatch[mno]=wn; reachKey[nk][wn]++; }
  }
  // final
  const fz=D.ko_struct.final; const fno=Object.keys(fz)[0]; const [m1,m2,venue]=fz[fno];
  let pl=null; if(ko[fno]!=null) pl=idx[ko[fno]];
  const champ=koWin(D,wmatch[m1],wmatch[m2],venue,r,pl);
  reach.champion[champ]++;
}

/* Run N sims. Returns probability tables. */
function runLive(D, opts){
  opts=opts||{};
  const N=opts.N||20000;
  const results=opts.results||{};   // {fixtureId:[hs,as]}
  const ko=opts.ko||{};             // {matchNo:winnerName}
  const r=mulberry32(opts.seed!=null?opts.seed:(1234567+Object.keys(results).length*7919+Object.keys(ko).length*104729));
  const P=buildIndex(D); const n=D.teams.length;
  const z=()=>new Float64Array(n);
  P._reach={r32:z(),r16:z(),qf:z(),sf:z(),final:z(),champion:z()};
  P.pos=Array.from({length:n},()=>[0,0,0,0]);
  // conditional next-match tracking for qualification scenarios (read-only; no effect on the sim)
  P.nextOf=new Int32Array(n).fill(-1); P.nextHome=new Uint8Array(n); P.fixNextTeams={};
  for(let ti=0;ti<n;ti++){ const t=D.teams[ti];
    for(let fi=0;fi<D.fixtures.length;fi++){ const f=D.fixtures[fi];
      if((f.home===t||f.away===t) && !results[f.id]){ const isHome=f.home===t; P.nextOf[ti]=f.id; P.nextHome[ti]=isHome?1:0;
        (P.fixNextTeams[f.id]=P.fixNextTeams[f.id]||[]).push({idx:ti,isHome}); break; } } }
  P.condTeams=[]; for(let i=0;i<n;i++) if(P.nextOf[i]>=0) P.condTeams.push(i);
  P.condN=new Float64Array(n*3); P.condAdv=new Float64Array(n*3); P.nextOutcome=new Int8Array(n);
  for(let s=0;s<N;s++) simOnce(D,P,results,ko,r);
  const out={};
  ["r32","r16","qf","sf","final","champion"].forEach(k=>{ out[k]={};
    D.teams.forEach((t,i)=> out[k][t]=P._reach[k][i]/N); });
  out.pos={}; D.teams.forEach((t,i)=> out.pos[t]=P.pos[i].map(x=>x/N));
  out.cond={};   // per team with an upcoming group match: P(advance | win/draw/lose it)
  for(let c=0;c<P.condTeams.length;c++){ const i=P.condTeams[c], t=D.teams[i]; const o={nextFix:P.nextOf[i], home:!!P.nextHome[i]};
    ["win","draw","lose"].forEach((kk,oi)=>{ const nn=P.condN[i*3+oi]; o[kk]={n:nn, p: nn>0? P.condAdv[i*3+oi]/nn : null}; });
    out.cond[t]=o; }
  out.N=N;
  return out;
}

/* Deterministic live group table from actual results only (for display). */
function liveTable(D, group, results){
  const gt=D.groups[group];
  const fx=D.fixtures.filter(f=>f.group===group);
  const row=gt.map(t=>({team:t,pld:0,w:0,d:0,l:0,gf:0,ga:0,pts:0}));
  const ri=Object.fromEntries(gt.map((t,i)=>[t,i]));
  const pgf={};
  fx.forEach(f=>{ const res=results[f.id]; if(!res)return; const [hs,as]=res;
    const x=ri[f.home],y=ri[f.away];
    row[x].pld++;row[y].pld++; row[x].gf+=hs;row[x].ga+=as; row[y].gf+=as;row[y].ga+=hs;
    if(hs>as){row[x].w++;row[y].l++;row[x].pts+=3;} else if(hs<as){row[y].w++;row[x].l++;row[y].pts+=3;}
    else {row[x].d++;row[y].d++;row[x].pts++;row[y].pts++;}
    pgf[x+","+y]=(pgf[x+","+y]||0)+hs; pgf[y+","+x]=(pgf[y+","+x]||0)+as; });
  row.forEach(o=>o.gd=o.gf-o.ga);
  const P=row.map(o=>o.pts), GD=row.map(o=>o.gd), GF=row.map(o=>o.gf);
  const order=rank2026(row.map((o,i)=>i), P, GD, GF, pgf, ()=>0.5);   // stable (no random) for a steady display order
  return order.map(i=>row[i]);
}

root.WCLive={runLive,liveTable,buildIndex,_mulberry32:mulberry32};
})(typeof module!=="undefined"&&module.exports?module.exports:(this.window=this.window||this,window));
