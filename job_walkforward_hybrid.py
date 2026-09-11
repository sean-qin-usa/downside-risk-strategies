# job_walkforward_hybrid.py -- ANNUAL-REFIT WALK-FORWARD FOR THE RESIDUAL-HYBRID FRONTIER (provenance repair).
# The manuscript quotes a residual-hybrid annual-refit frontier (+2.09% top decile, DM 4.43; overall -0.18%)
# for which no result file is committed; walkforward_results.json is the returns-space learner
# (job_walkforward.py: RAWX features, raw-return target). This job runs the identical schedule
# (Jan-1 cutoffs 2020-2024, per-name GARCH-t refit on expanding data, residuals and mk63 rebuilt
# under the refit parameters) with the RESIDUAL-HYBRID learner of job_composite.py: pooled boosted
# residual quantiles on ZX=[logsig,zl1,absz5,zstd21,fracdn5], forecast = mu + sig * q_z. No EVT,
# no conformal shift, matching the frontier headline. Output walkforward_hybrid_results.json.
# Set GBC_PROJ to override the project path. Self-test: --synthetic.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
import sys
try:
    from arch import arch_model; GARCH_BACKEND="arch"
except ImportError:
    GARCH_BACKEND="builtin_qml"
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"garch_fallback.py")).read())
P=os.environ.get("GBC_PROJ",r"C:\Users\OWNER\Claude\Projects\GBC Project"); SYN="--synthetic" in sys.argv; t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
if SYN:
    rng=np.random.default_rng(3); recs=[]; dates=pd.bdate_range("2014-01-02",periods=2770)
    for pn in range(12):
        om,al,be,nu=0.04,0.08,0.90,5.0+rng.uniform(0,3); s2=np.empty(2770); e=np.empty(2770); s2[0]=om/(1-al-be)
        for k in range(2770):
            if k: s2[k]=om+al*e[k-1]**2+be*s2[k-1]
            zz=stats.t.rvs(nu,random_state=rng)/math.sqrt(nu/(nu-2))
            if rng.uniform()<0.02: zz-=rng.exponential(2.5)
            e[k]=math.sqrt(s2[k])*zz
        recs.append(pd.DataFrame({'permno':pn,'date':dates,'ret':(0.02+e)/100.0}))
    rr=pd.concat(recs)
else:
    rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
series={}
for pn in names:
    g=rr[rr.permno==pn].sort_values('date')
    series[pn]=(g['ret'].values.astype(float),pd.to_datetime(g['date'].values))
years=sorted({d.year for _,(y,dts) in series.items() for d in [dts[-1]]})
# test years: roughly the frozen protocol's last 40% -> 2020..2024 on the 2014-24 panel
TESTYEARS=[2020,2021,2022,2023,2024]
rows=[]
for ty in TESTYEARS:
    cut=pd.Timestamp(f"{ty}-01-01")
    TR=[]; TEyr=[]
    for pn,(y,dts) in series.items():
        sp=int(np.searchsorted(dts,cut))
        te_end=int(np.searchsorted(dts,pd.Timestamp(f"{ty+1}-01-01")))
        if sp<(300 if SYN else 750) or te_end-sp<30: continue
        try:
            res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
            p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
        except Exception: continue
        n=te_end
        e=y[:n]-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
        for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
        sig=np.sqrt(s2); z=(y[:n]-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
        df=pd.DataFrame({'y':y[:n],'sig':sig,'z':z,'date':dts[:n]})
        df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
        df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
        df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
        df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
        df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
        df['idx']=np.arange(n); df=df.dropna(subset=ZX+['mk63'])
        trn=df[df['idx']<sp]; tst=df[df['idx']>=sp]
        if len(tst)<10: continue
        TR.append(trn[ZX+['z']])
        te=tst[ZX+['y','sig','mk63','date']].copy(); te['mu']=mu; te['nu']=nu; te['tsc']=tsc; te['permno']=pn
        TEyr.append(te)
    TRc=pd.concat(TR); TEc=pd.concat(TEyr).reset_index(drop=True)
    lg("cut %s: %d names, %dk train rows, %d test rows %.0fs"%(cut.date(),TEc.permno.nunique(),len(TRc)//1000,len(TEc),time.time()-t0))
    GQ={}
    for t in TAUS:
        m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[ZX].values,TRc['z'].values)
        GQ[t]=m.predict(TEc[ZX].values)
    Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
    pl_g=np.mean([pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t) for t in TAUS],axis=0)
    pl_b=np.mean([pin(Y,MU+SIG*GQ[t],t) for t in TAUS],axis=0)
    ydf=pd.DataFrame({'edge':pl_g-pl_b,'plg':pl_g,'mk':TEc['mk63'].values,'date':TEc['date'].values})
    rows.append(ydf)
ALL=pd.concat(rows).reset_index(drop=True)
lg("walk-forward panel assembled: %d rows, %d dates %.0fs"%(len(ALL),ALL['date'].nunique(),time.time()-t0))
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
ok=np.isfinite(ALL['mk'].values)
dec=np.full(len(ALL),-1); dec[ok]=pd.qcut(ALL['mk'].values[ok],10,labels=False,duplicates='drop')
prof=[]
for d in range(10):
    m5=dec==d
    prof.append(round(100*float(ALL['edge'].values[m5].mean())/float(ALL['plg'].values[m5].mean()),2) if m5.sum()>500 else None)
top=dec==9
s=ALL[top].groupby('date')['edge'].mean()
sall=ALL.groupby('date')['edge'].mean()
OUT={'note':'RESIDUAL-HYBRID annual walk-forward (frontier learner of job_composite.py: pooled boosted residual quantiles, forecast mu+sig*q_z, no EVT/conformal): at each Jan-1 cutoff 2020-2024, per-name GARCH refit on expanding pre-cutoff data, features and mk63 rebuilt under the refit parameters, pooled GBM retrained on pre-cutoff rows, next calendar year predicted. Kills the stale-parameterization alternative: no stage carries stale estimates into test.',
     'test_years':TESTYEARS,'n_test':int(len(ALL)),'n_dates':int(len(sall)),
     'overall_edge_pct':round(100*float(ALL['edge'].mean())/float(ALL['plg'].mean()),2),
     'overall_DM':nw_t(sall.values),
     'decile_profile_edge_pct':prof,
     'top_decile_edge_pct':round(100*float(ALL['edge'].values[top].mean())/float(ALL['plg'].values[top].mean()),2),
     'top_decile_DM':nw_t(s.values),'top_decile_n_dates':int(len(s)),
     'top_decile_NWlag_sensitivity':{('lag%d'%L):nw_t(s.values,L) for L in (5,10,20,44)}}
json.dump(OUT,open(os.path.join(P,"walkforward_hybrid_results_synthetic.json" if SYN else "walkforward_hybrid_results.json"),"w"),indent=2)
OUT['garch_backend']=GARCH_BACKEND; lg("WALKFORWARDHYBRIDDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1))
