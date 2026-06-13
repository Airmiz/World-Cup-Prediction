/* In-play win-probability model.
 * Given pre-match expected goals (lh, la) and the current score at minute t,
 * remaining goals over the time left are independent Poisson with mean scaled
 * by the remaining fraction. P(home/draw/away) follows exactly by convolution.
 * Pure functions; usable in Node (tests) and the browser.
 */
(function (root) {
"use strict";

function poissonPmf(mean, K){
  const out=new Array(K+1); let p=Math.exp(-mean); out[0]=p;
  for(let k=1;k<=K;k++){ p*=mean/k; out[k]=p; } return out;
}

/* Win/draw/loss probabilities at `minute` given current score (gh,ga). */
function probs(lh, la, gh, ga, minute, fullMin){
  fullMin=fullMin||90;
  const f=Math.max(0,(fullMin-minute)/fullMin);
  if(f<=0){ return gh>ga?[1,0,0]:gh<ga?[0,0,1]:[0,1,0]; }
  const K=12, ph=poissonPmf(lh*f,K), pa=poissonPmf(la*f,K);
  let H=0,D=0,A=0;
  for(let i=0;i<=K;i++) for(let j=0;j<=K;j++){
    const w=ph[i]*pa[j], fh=gh+i, fa=ga+j;
    if(fh>fa)H+=w; else if(fh===fa)D+=w; else A+=w;
  }
  const s=H+D+A; return [H/s,D/s,A/s];
}

/* Score after applying goal events with minute <= t. events:[{min,team}] team:'home'|'away' */
function scoreAt(events, t){
  let h=0,a=0; for(const e of events){ if(e.min<=t){ (e.team==="home")?h++:a++; } } return [h,a];
}

/* Build a 0..fullMin timeline (per-minute) of [H,D,A] given events. */
function timeline(lh, la, events, fullMin){
  fullMin=fullMin||90; const T=[];
  for(let m=0;m<=fullMin;m++){ const [gh,ga]=scoreAt(events,m); T.push({m, p:probs(lh,la,gh,ga,m,fullMin), gh, ga}); }
  return T;
}

/* Sample a plausible match story (goal minutes) from the model for a not-yet-played
 * fixture: draw a final scoreline ~ Poisson(lh),Poisson(la), then place each goal at
 * a uniformly random minute. Deterministic if a seeded rng is passed. */
function simulateStory(lh, la, rng){
  rng=rng||Math.random;
  const draw=mean=>{ const L=Math.exp(-mean); let k=0,p=1; do{k++;p*=rng();}while(p>L); return k-1; };
  const gh=draw(lh), ga=draw(la); const ev=[];
  for(let i=0;i<gh;i++) ev.push({min:1+Math.floor(rng()*90),team:"home"});
  for(let i=0;i<ga;i++) ev.push({min:1+Math.floor(rng()*90),team:"away"});
  ev.sort((x,y)=>x.min-y.min);
  return ev;
}

root.WCInPlay={probs,timeline,scoreAt,simulateStory,_poissonPmf:poissonPmf};
})(typeof module!=="undefined"&&module.exports?module.exports:(this.window=this.window||this,window));
