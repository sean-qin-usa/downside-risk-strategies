# job_calendar_split.py -- THE definitive answer to the calendar-overlap/leakage attack.
# Single calendar-time split for the whole panel: everything (GARCH fits, pooled learner,
# GPD tail) estimated on data STRICTLY BEFORE 2020-01-01; test = 2020-01-01 onward for all
# names simultaneously. No name's training window overlaps any name's test window in
# calendar time, so no common-shock leakage channel exists. Re-runs the frontier decile
# profile and the engine-vs-desk pinball comparison under this split.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
CUT=pd.Timestamp("2020-01-01")
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
RAWX=['lag1','abs1','prv5','prv21','rv63']
TR=[]; TE=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=pd.to_datetime(g['date'].values); n=len(y)
    sp=int(np.searchsorted(dts, CUT))          # calendar split index for THIS name
    if sp<750 or n-sp<250: continue            # need real pre-2020 history and post-2020 test
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    ztr=z[:sp]
    for t in [0.5]: pass
    df['fhs_q']=0.0
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=RAWX+['mk63'])
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<100: continue
    TR.append(trn[RAWX+['y']])
    keep=RAWX+['y','sig','date','mu','nu','tsc','mk63']
    t2=tst[keep].copy(); t2['permno']=pn
    t2['fhs01']=mu+t2['sig']*float(np.quantile(ztr,0.01)); t2['fhs025']=mu+t2['sig']*float(np.quantile(ztr,0.025))
    TE.append(t2)
lg("panels %d %.0fs (calendar cut %s)"%(len(TE),time.time()-t0,CUT.date()))
TRc=pd.concat(TR); TEc=pd.concat(TE).reset_index(drop=True)
GQ={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['y'].values)
    GQ[t]=m.predict(TEc[RAWX].values)
    if t in (0.01,0.5,0.99): lg("  tau %.3f %.0fs"%(t,time.time()-t0))
Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
pl_g=np.mean([pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t) for t in TAUS],axis=0)
pl_b=np.mean([pin(Y,GQ[t],t) for t in TAUS],axis=0)
edge=pl_g-pl_b
dates=TEc['date'].values; mk=TEc['mk63'].values
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
ok=np.isfinite(mk)
dec=pd.qcut(mk[okg:=ok],10,labels=False,duplicates='drop')
prof=[]
for d in sorted(np.unique(dec)):
    m5=(dec==d)
    prof.append(round(100*float(edge[ok][m5].mean())/float(pl_g[ok][m5].mean()),2))
top=ok.copy(); top[ok]= (dec==9)
s=pd.DataFrame({'d':edge[top],'date':dates[top]}).groupby('date')['d'].mean()
t_top=nw_t(s.values)
sall=pd.DataFrame({'d':edge,'date':dates}).groupby('date')['d'].mean()
OUT={'note':'Single calendar-time split (train strictly < 2020-01-01, test >= for ALL names): no calendar overlap between any training and any test window. Frontier decile profile + overall edge under this split.',
     'cut':'2020-01-01','n_names':int(TEc.permno.nunique()),'n_test':int(len(Y)),'n_dates':int(len(sall)),
     'overall_edge_pct':round(100*float(edge.mean())/float(pl_g.mean()),2),'overall_DM':nw_t(sall.values),
     'decile_profile_edge_pct':prof,'top_decile_DM':t_top,'top_decile_n_dates':int(len(s))}
json.dump(OUT,open(os.path.join(P,"calendar_split_results.json"),"w"),indent=2)
lg("CALSPLITDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=2))
