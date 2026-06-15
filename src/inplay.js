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

// Red-card effect on remaining-goal rates. A team reduced to 10 men scores at a
// reduced rate and concedes at a raised rate for the rest of the match — a large,
// well-established effect the score-only model ignores. Conservative per-card
// multipliers (a sending-off ≈ a ~0.5-goal swing over a half).
const RC_DOWN=0.74, RC_UP=1.24;
// Live shot dominance as a mild xG proxy: a team out-creating the other has been
// the better side, nudging its remaining rate. Capped and secondary to the score.
function shotMult(share){ return 1 + Math.max(-0.16, Math.min(0.16, (share-0.5)*0.5)); }

/* Win/draw/loss probabilities at `minute` given current score (gh,ga).
 * Optional st = {hr, ar, hsot, asot}: home/away red cards and shots-on-target so far. */
function probs(lh, la, gh, ga, minute, fullMin, st){
  fullMin=fullMin||90;
  let lhf=lh, laf=la;
  if(st){
    const hr=st.hr||0, ar=st.ar||0;
    if(hr||ar){                                            // man-advantage adjustment
      lhf *= Math.pow(RC_UP, ar) * Math.pow(RC_DOWN, hr);
      laf *= Math.pow(RC_UP, hr) * Math.pow(RC_DOWN, ar);
    }
    if(st.hsot!=null && st.asot!=null){                    // shot-dominance momentum (capped)
      const tot=st.hsot+st.asot;
      if(tot>=4){ const m=shotMult(st.hsot/tot); lhf*=m; laf*=(2-m); }
    }
  }
  // remaining-goal rate stays per-90 (lh/90 per minute); the match window may extend past
  // 90 into stoppage time, so scale by remaining minutes / 90 (identical to the old form when
  // fullMin==90). Only a truly finished match (minute>=fullMin) locks to the current scoreline.
  const rem=Math.max(0, fullMin-minute), f=rem/90;
  if(rem<=0){ return gh>ga?[1,0,0]:gh<ga?[0,0,1]:[0,1,0]; }
  const K=12, ph=poissonPmf(lhf*f,K), pa=poissonPmf(laf*f,K);
  let H=0,D=0,A=0;
  for(let i=0;i<=K;i++) for(let j=0;j<=K;j++){
    const w=ph[i]*pa[j], fh=gh+i, fa=ga+j;
    if(fh>fa)H+=w; else if(fh===fa)D+=w; else A+=w;
  }
  const s=H+D+A; return [H/s,D/s,A/s];
}

/* Red-card counts on each side as of minute t. reds:[{min,team}] */
function redsAt(reds, t){
  let hr=0, ar=0; for(const e of (reds||[])){ const m=e.min+(e.add||0); if(m<=t){ (e.team==="home")?hr++:ar++; } } return {hr, ar};
}

/* Score after applying goal events with minute <= t. events:[{min,team}] team:'home'|'away' */
function scoreAt(events, t){
  let h=0,a=0; for(const e of events){ const m=e.min+(e.add||0); if(m<=t){ (e.team==="home")?h++:a++; } } return [h,a];
}

/* Build a 0..fullMin timeline (per-minute) of [H,D,A] given events.
 * Optional reds:[{min,team}] applies the man-advantage as of each minute, so the
 * curve correctly jumps when a player is sent off. */
function timeline(lh, la, events, fullMin, reds){
  fullMin=fullMin||90; const T=[];
  for(let m=0;m<=fullMin;m++){ const [gh,ga]=scoreAt(events,m);
    const st=(reds&&reds.length)?redsAt(reds,m):null;
    T.push({m, p:probs(lh,la,gh,ga,m,fullMin,st), gh, ga}); }
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

root.WCInPlay={probs,timeline,scoreAt,redsAt,simulateStory,_poissonPmf:poissonPmf};
})(typeof module!=="undefined"&&module.exports?module.exports:(this.window=this.window||this,window));
