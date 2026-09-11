# REGIME-DETECTOR LATENCY (ai2) — "how fast is the regime detector by lag?"
# Two questions: (1) DETECTION LATENCY — when a genuine turbulent regime begins, how many days until each causal detector
# fires? (2) EDGE-VS-ACTION-LAG — if you only switch to the nonparam model L days after the regime starts, how much of the
# turbulent-regime edge survives? Together they say how fast the detector must be and how fast it actually is.
# Detectors (all causal, lag1): EWMA vol lam=0.94 & 0.97; rolling std 5/21/63d. TRUTH regime = forward-10d realized vol in
# the name's top 20% (a real vol spike). Onset = first day of a turbulent run. Threshold per detector = its train 80th pct.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
lg("names=%d %.0fs"%(len(names),time.time()-t0))
def ewma_vol(y,lam):
    v=np.empty(len(y)); v[0]=y[0]**2
    for i in range(1,len(y)): v[i]=lam*v[i-1]+(1-lam)*y[i-1]**2
    return np.sqrt(v)
DET={'ewma94':None,'ewma97':None,'std5':None,'std21':None,'std63':None}
lags={k:[] for k in DET}; prec={k:[0,0] for k in DET}; rec={k:[0,0] for k in DET}   # prec=[tp,fp] rec=[detected_onsets,total_onsets]
# edge-vs-action-lag accumulators
edge_by_L={L:[] for L in range(0,6)}; base_calm=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    s=pd.Series(y)
    sig_det={'ewma94':ewma_vol(y,0.94),'ewma97':ewma_vol(y,0.97),
             'std5':s.rolling(5,min_periods=3).std().shift(1).values,
             'std21':s.rolling(21,min_periods=8).std().shift(1).values,
             'std63':s.rolling(63,min_periods=20).std().shift(1).values}
    # truth: forward-10d realized vol, top 20% = turbulent
    fwd=pd.Series(y).rolling(10).std().shift(-10).values
    thr_true=np.nanquantile(fwd[:sp],0.8)
    turb=fwd>=thr_true
    # onsets (calm->turb transitions), in test region
    onsets=[i for i in range(sp,n-10) if turb[i] and not turb[i-1]]
    for k in DET:
        thr=np.nanquantile(sig_det[k][:sp][np.isfinite(sig_det[k][:sp])],0.8)
        flags=sig_det[k]>=thr
        # detection lag per onset: first day in [onset, onset+15] where flags True
        for o in onsets:
            rec[k][1]+=1; win=range(o,min(o+16,n))
            hit=[j for j in win if np.isfinite(sig_det[k][j]) and flags[j]]
            if hit: lags[k].append(hit[0]-o); rec[k][0]+=1
        # precision over test days: of flagged days, how many are truly turbulent
        tst=np.arange(sp,n-10); fl=flags[tst]&np.isfinite(sig_det[k][tst])
        prec[k][0]+=int((fl&turb[tst]).sum()); prec[k][1]+=int((fl&~turb[tst]).sum())
    # ---- edge vs action lag: need GBM & GARCH pinball on test days ----
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for i in range(1,n): s2[i]=max(om+al*e[i-1]**2+be*s2[i-1],1e-8)
    sigp=np.sqrt(s2); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    # cheap per-name nonparam = FHS_recent on standardized resid (adapts to shape) as the "switch-to" model
    z=(y-mu)/np.maximum(sigp,1e-6)
    # days-since-onset for each turbulent day (0 on the onset day), -1 for calm
    dsince=np.full(n,-1); d=-1
    for i in range(sp,n-10):
        if turb[i]: d=(d+1) if (i>0 and turb[i-1]) else 0; dsince[i]=d
        else: d=-1
    for i in range(sp,n-10):
        sg=sigp[i]; lo=max(0,i-250); zr=z[lo:i]
        if len(zr)<50: continue
        yi=y[i]
        qg={t:mu+sg*stats.t.ppf(t,nu)/tsc for t in TAUS}; qb={t:mu+sg*np.quantile(zr,t) for t in TAUS}
        ed=np.mean([pin(yi,qg[t],t) for t in TAUS])-np.mean([pin(yi,qb[t],t) for t in TAUS])  # >0 => nonparam better
        if dsince[i]<0: base_calm.append(ed)
        else:
            for L in range(0,6):
                if dsince[i]>=L: edge_by_L[L].append(ed)     # switched if days-since-onset >= action lag L
    if len(edge_by_L[0])>300000: break
def summ_lag(k):
    a=np.array(lags[k]); tp,fp=prec[k]; det,tot=rec[k]
    return dict(median_lag_days=float(np.median(a)) if len(a) else None,
                mean_lag_days=round(float(np.mean(a)),2) if len(a) else None,
                recall=round(det/tot,3) if tot else None,
                precision=round(tp/(tp+fp),3) if (tp+fp) else None,
                n_onsets=tot)
out={'note':'Regime-detector latency. TRUTH turbulent = forward-10d realized vol in name top 20%; onset=calm->turb. '
            'Detectors causal(lag1): EWMA lam0.94/0.97, rolling std 5/21/63. median/mean detection lag in trading days, '
            'plus precision/recall. edge_vs_action_lag = mean (GARCH_pin - nonparam_pin) on turbulent days if you switch '
            'to nonparam L days after onset (L=0 immediate). base_calm_edge = same on calm days (should be ~0/negative).',
     'detection':{k:summ_lag(k) for k in DET},
     'edge_vs_action_lag':{('L%d'%L):round(float(np.mean(edge_by_L[L])),5) for L in range(0,6) if edge_by_L[L]},
     'base_calm_edge':round(float(np.mean(base_calm)),5) if base_calm else None,
     'takeaway':'Compare detection lag (how fast it fires) against edge_vs_action_lag decay (how fast the edge fades) to '
                'see whether a realistic detector is fast enough to capture the turbulent-regime edge.'}
json.dump(out,open(os.path.join(D,"detector_latency_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
