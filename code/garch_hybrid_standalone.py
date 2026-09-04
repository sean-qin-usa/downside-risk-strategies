# STANDALONE GARCH-residual hybrid (ai2) — tests the "never worse than GARCH on a single asset" property, and
# fixes the FHS calibration flagged in the industry battery. Per-NAME (no pooling): fit GARCH-t, get sigma_t path,
# standardized residuals z. Then form the residual-quantile Qz three ways and reconstruct q=mu+sigma_t*Qz(tau):
#   (a) parametric t  == plain GARCH-t
#   (b) FHS_full : empirical quantile of ALL train standardized residuals (classic filtered historical simulation)
#   (c) FHS_recent : empirical quantile of the last 250 standardized residuals up to t (adapts to residual-shape drift)
# Predict: FHS variants >= GARCH-t where the standardized-residual shape departs from Student-t (the misspecification
# regime); ties it otherwise. If so, the residual-hybrid gives nonparam a "never materially worse than GARCH" floor standalone.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False)
names=cnt[cnt>=1500].index.tolist()[:200]
lg("names=%d  %.0fs"%(len(names),time.time()-t0))
agg={m:{k:[] for k in ['overall','Q1_calm','Q5_turbulent','breach5']} for m in ['garch_t','fhs_full','fhs_recent']}
rk=[]                                        # per-name residual kurtosis (the misspecification metric)
nn=0
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception:
        continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6)
    tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    ztr=z[:sp]; rk.append(float(pd.Series(ztr).kurtosis()))   # excess kurtosis of standardized residuals (train)
    # precompute empirical residual quantiles
    qfull={t:np.quantile(ztr,t) for t in TAUS}
    prv21=pd.Series(y).rolling(21,min_periods=8).std().shift(1).values
    idx=np.arange(sp,n)
    # vol quintile thresholds from test prv21
    pv=prv21[idx]; ok=~np.isnan(pv)
    if ok.sum()<30: continue
    q1thr=np.nanquantile(pv,0.2); q5thr=np.nanquantile(pv,0.8)
    for m in ['garch_t','fhs_full','fhs_recent']:
        pl=[]; plq1=[]; plq5=[]; br=0; c=0
        for i in idx:
            if np.isnan(prv21[i]): continue
            yi=y[i]; s=sig[i]
            if m=='garch_t':
                qs={t:mu+s*stats.t.ppf(t,nu)/tsc for t in TAUS}
            elif m=='fhs_full':
                qs={t:mu+s*qfull[t] for t in TAUS}
            else:
                lo=max(0,i-250); zr=z[lo:i]
                if len(zr)<50: zr=ztr
                qs={t:mu+s*np.quantile(zr,t) for t in TAUS}
            pv_=np.mean([pin(yi,qs[t],t) for t in TAUS]); pl.append(pv_)
            if prv21[i]<=q1thr: plq1.append(pv_)
            if prv21[i]>=q5thr: plq5.append(pv_)
            br+=(yi<qs[0.05]); c+=1
        agg[m]['overall'].append(np.mean(pl)); agg[m]['breach5'].append(br/c)
        if plq1: agg[m]['Q1_calm'].append(np.mean(plq1))
        if plq5: agg[m]['Q5_turbulent'].append(np.mean(plq5))
    nn+=1
    if nn%50==0: lg("  %d names  %.0fs"%(nn,time.time()-t0))
def summ(m): return {k:round(float(np.mean(v)),4) for k,v in agg[m].items() if v}
out={'note':'Standalone (per-name) GARCH-residual hybrid on CRSP (%d names). GARCH-t vs FHS_full vs FHS_recent(250). '
            'q=mu+sigma_t*Qz(tau); Qz parametric-t / empirical-full / empirical-recent. Tests whether residual-space '
            'nonparam gives a "never worse than GARCH standalone" floor and wins under residual-shape misspecification. '
            'Also = a clean FHS (fixes the battery FHS calibration bug).'%nn,
     'n_names':nn,'mean_resid_excess_kurtosis':round(float(np.nanmean(rk)),2),
     'garch_t':summ('garch_t'),'fhs_full':summ('fhs_full'),'fhs_recent':summ('fhs_recent')}
# improvement of best FHS over garch
def impr(a,b): return round(100*(b-a)/b,2)
bestfhs={k:min(out['fhs_full'].get(k,9),out['fhs_recent'].get(k,9)) for k in ['overall','Q1_calm','Q5_turbulent']}
out['bestFHS_vs_garch_pct']={k:impr(bestfhs[k],out['garch_t'][k]) for k in bestfhs}
json.dump(out,open(os.path.join(D,"garch_hybrid_standalone_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
