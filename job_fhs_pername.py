# job_fhs_pername.py -- THE BANK-EXACT FHS BENCHMARK (per-name, plus rolling).
# The main battery's "fhs" row uses the POOLED train-residual quantile (unconditional
# pooled shape) -- a legitimate comparator, but not the textbook desk implementation,
# which filters EACH series and uses THAT series' own standardized-residual history.
# This job adds, on the identical 140-name panel, split, and 12-tau pinball:
#   fhs_pername   = GARCH sigma x per-name TRAIN-window empirical z-quantile (constant)
#   fhs_roll500   = GARCH sigma x per-name ROLLING 500-day z-quantile (shift(1), causal)
#   fhs_pooled    = the battery's original pooled variant (same-run reference)
#   garch_t, resid_hybrid_ML (same-run reference)
# DM vs the hybrid, pooled Kupiec/Christoffersen at 99% and 97.5%.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:140]
RAWX=['lag1','abs1','prv5','prv21','rv63']; ZX=['logsig','zl1','absz5','zstd21','fracdn5']
TR_z=[]; rows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1); df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1); df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    zs=pd.Series(z)
    ztr=z[:sp]
    for t in TAUS:
        df['pn_%g'%t]=float(np.quantile(ztr,t))                              # per-name train constant
        df['rl_%g'%t]=zs.rolling(500,min_periods=250).quantile(t).shift(1)   # per-name rolling, causal
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=RAWX+ZX+['rl_%g'%TAUS[0]])
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TR_z.append(trn[ZX+['z']])
    keep=['y','sig','date','mu','nu','tsc']+ZX+['pn_%g'%t for t in TAUS]+['rl_%g'%t for t in TAUS]
    t2=tst[keep].copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TR_z)
ZQ={}
for t in TAUS:
    mz=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=mz.predict(TE[ZX].values)
    if t in (0.005,0.5,0.99): lg("  ztau %.3f %.0fs"%(t,time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
MODELS=['garch_t','fhs_pooled','fhs_pername','fhs_roll500','resid_hybrid_ML']
Q={m:{} for m in MODELS}
for t in TAUS:
    Q['garch_t'][t]=MU+SIG*stats.t.ppf(t,NU)/TSC
    Q['fhs_pooled'][t]=MU+SIG*np.quantile(TRzc['z'].values,t)
    Q['fhs_pername'][t]=MU+SIG*TE['pn_%g'%t].values
    Q['fhs_roll500'][t]=MU+SIG*TE['rl_%g'%t].values
    Q['resid_hybrid_ML'][t]=MU+SIG*ZQ[t]
def pinball_avg(m):
    pl=np.zeros(len(Y))
    for t in TAUS: pl+=pin(Y,Q[m][t],t)
    return pl/len(TAUS)
PL={m:pinball_avg(m) for m in MODELS}
def _llb(pp,k0,k1):
    if k0+k1==0: return 0.0
    if pp<=0: return 0.0 if k1==0 else -1e300
    if pp>=1: return 0.0 if k0==0 else -1e300
    return k0*math.log(1-pp)+k1*math.log(pp)
def kupiec(x,T,p):
    if x==0 or x==T: return None
    pi=x/T; lr=-2*(_llb(p,T-x,x)-_llb(pi,T-x,x)); return round(float(1-stats.chi2.cdf(max(lr,0),1)),4)
def nw_var(d,lag=10):
    d=d-d.mean(); Tn=len(d); v=np.mean(d*d)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(d[k:]*d[:-k])
    return v/Tn
summary={}; T=len(Y)
Ldate=pd.DataFrame({m:PL[m] for m in MODELS}); Ldate['date']=TE['date'].values
Lmat=Ldate.groupby('date').mean()[MODELS]; L=Lmat.values
mi={m:i for i,m in enumerate(MODELS)}; hb=mi['resid_hybrid_ML']
for m in MODELS:
    b99=(Y<Q[m][0.01]); b975=(Y<Q[m][0.025])
    row=dict(avg_pinball=round(float(PL[m].mean()),4),
             breach99=round(float(b99.mean()),4), breach975=round(float(b975.mean()),4),
             kupiec99_p=kupiec(int(b99.sum()),T,0.01), kupiec975_p=kupiec(int(b975.sum()),T,0.025))
    if m!='resid_hybrid_ML':
        d=L[:,mi[m]]-L[:,hb]
        s=d.mean()/math.sqrt(max(nw_var(d),1e-12))
        row['DM_vs_hybrid']=round(float(s),2); row['p_one_sided']=round(float(1-stats.norm.cdf(s)),4)
    summary[m]=row
OUT={'note':'Per-name FHS restatement on the identical 140-name battery panel: per-name train-constant and per-name rolling-500d causal z-quantiles vs the pooled variant, GARCH-t, and the hybrid. DM_vs_hybrid>0 means the row model is worse than the hybrid.',
     'n_names':int(TE['permno'].nunique()),'n_test_rows':int(len(Y)),
     'per_model':summary}
json.dump(OUT,open(os.path.join(P,"fhs_pername_results.json"),"w"),indent=2)
lg("FHSPERNAMEDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1))
