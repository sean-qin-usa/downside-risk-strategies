# job_causal_frontier.py -- THE HEADLINE FRONTIER UNDER A STRICTLY CAUSAL DECILE RULE.
# Adversarial review [FATAL #1]: the canonical frontier forms deciles with pd.qcut over
# the WHOLE pooled test panel, so an asset's "top decile" membership depends on the
# full-sample score distribution (including future dates). The raw mk63 inputs are causal
# (rolling kurtosis .shift(1)), but the classification is not real-time. This job recomputes
# the design-era top-decile edge under two decile rules that use NO future information, and
# compares to the global-qcut headline on the same panel and engine:
#   (A) global qcut  -- the shipped rule (baseline for comparison)
#   (B) expanding pooled threshold -- at each date t, flag assets whose mk63 exceeds the
#       90th percentile of ALL mk63 observed on dates strictly < t (250-date burn-in).
#       This is the "as deployed" real-time rule Algorithm 4 describes.
#   (C) within-date cross-sectional top decile -- rank assets against each other on date t
#       only. Unambiguously real-time; no temporal pooling at all.
# Engine and panel identical to job_fz_fullpanel / job_nurel (200 names, GARCH y[:sp],
# pooled GBM shape on trn residuals, 11-tau average pinball; edge=(garch-engine)/garch).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
TRz=[]; rows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e0=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e0[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=ZX+['mk63'])
    trn=dd[dd['idx']<cp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TRz.append(trn[ZX+['z']]); t2=tst.copy(); t2['permno']=pn; rows.append(t2)
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz)
lg("panel %d names %d rows %.0fs"%(TE.permno.nunique(),len(TE),time.time()-t0))
ZQ={}
for t in TAUS:
    ZQ[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values).predict(TE[ZX].values)
    lg("  tau %.3f %.0fs"%(t,time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
plE=np.zeros(len(Y)); plG=np.zeros(len(Y))
for t in TAUS:
    plE+=pin(Y,MU+SIG*ZQ[t],t); plG+=pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t)
plE/=len(TAUS); plG/=len(TAUS)
d=plG-plE; dates=pd.to_datetime(TE['date'].values); mk=TE['mk63'].values
def edge(mask):
    if mask.sum()<30: return None
    dd_=pd.DataFrame({'d':d[mask],'date':dates[mask]}).groupby('date')['d'].mean()
    return {'edge_pct':round(100*float(d[mask].mean())/float(plG[mask].mean()),3),'DM':nw_t(dd_.values),'n':int(mask.sum())}
# (A) global qcut (shipped)
ok=np.isfinite(mk); q=np.full(len(Y),-1); q[ok]=pd.qcut(pd.Series(mk[ok]),10,labels=False,duplicates='drop').values
A_top=(q==q[q>=0].max()); A_bot=(q==0)
# (B) expanding pooled threshold (250-date burn-in)
di,udates=pd.factorize(dates,sort=True); di=np.asarray(di)
BURN=250
by_date={}
for i in range(len(Y)):
    by_date.setdefault(di[i],[]).append(mk[i])
prior=[]; ndates_seen=0; thr_by_date={}
for dd in range(len(udates)):
    thr_by_date[dd]=(np.nanpercentile(prior,90) if ndates_seen>=BURN else np.nan)
    vs=[v for v in by_date.get(dd,[]) if np.isfinite(v)]
    if vs: prior.extend(vs); ndates_seen+=1
B_thr=np.array([thr_by_date[di[i]] for i in range(len(Y))])
B_top=np.isfinite(B_thr)&(mk>=B_thr); B_defined=np.isfinite(B_thr)
# (C) within-date cross-sectional top decile
tmp=pd.DataFrame({'mk':mk,'di':di})
def _wd(gr):
    m=gr['mk'].values; okk=np.isfinite(m)
    out=np.zeros(len(m),bool)
    if okk.sum()>=10:
        thr90=np.nanpercentile(m[okk],90); out=okk&(m>=thr90)
    return pd.Series(out,index=gr.index)
C_top=tmp.groupby('di',group_keys=False).apply(_wd).values.astype(bool)
OUT={'note':('Design-era headline frontier under causal decile rules. (A) global qcut = shipped rule; '
  '(B) expanding pooled 90th-pct threshold over strictly-earlier dates (250-date burn-in), the as-deployed '
  'real-time rule; (C) within-date cross-sectional top decile (rank assets within each date only). '
  'Engine/panel identical to fz_fullpanel. edge=(garch-engine)/garch avg 11-tau pinball, per-date NW(10) DM. '
  'If B and C reproduce A, the global-qcut classification introduces no material future information.'),
 'n_rows':int(len(Y)),'n_names':int(TE.permno.nunique()),
 'A_global_qcut':{'top':edge(A_top),'bottom':edge(A_bot),'overall':edge(np.ones(len(Y),bool))},
 'B_expanding_threshold':{'top':edge(B_top),'top_within_defined_region':edge(B_top),
                          'n_defined':int(B_defined.sum()),'overall_defined':edge(B_defined)},
 'C_within_date_topdecile':{'top':edge(C_top)},
 'overlap_A_top_vs_B_top':round(float((A_top&B_top).sum()/max(A_top.sum(),1)),3),
 'overlap_A_top_vs_C_top':round(float((A_top&C_top).sum()/max(A_top.sum(),1)),3)}
json.dump(OUT,open(os.path.join(P,"causal_frontier_results.json"),"w"),indent=2)
lg("CAUSALFRONTIERDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1))
