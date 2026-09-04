# job_romanowolf_v2.py -- FWER control over the whole frontier grid (v2: date-index fix).
# v1 crashed: dict keys became np.datetime64 while lookups were pd.Timestamp (KeyError).
# v2 uses pure-numpy searchsorted on datetime64 values. Also adds a block-length
# sensitivity pass (blk=20, B=1000) alongside the primary (blk=10, B=2000).
# Hypotheses: per-date mean edge (GARCH-t minus pooled learner, 11-tau pinball) in each of
# 10 deciles x 3 signals (mk63, skew63, jump5) = 30 one-sided hypotheses "edge > 0".
# Romano-Wolf step-down, stationary bootstrap over DATES (preserves cross-hypothesis dependence).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
RAWX=['lag1','abs1','prv5','prv21','rv63']
TR=[]; TE=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
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
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().shift(1).abs()
    df['idx']=np.arange(n)
    dd=df.dropna(subset=RAWX+['mk63','jump5','skew63'])
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<30: continue
    TR.append(trn[RAWX+['y']])
    t2=tst[RAWX+['y','sig','date','mk63','jump5','skew63']].copy()
    t2['mu']=mu; t2['nu']=nu; t2['tsc']=tsc
    TE.append(t2)
lg("panels %d %.0fs"%(len(TE),time.time()-t0))
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
dvals=pd.to_datetime(TEc['date'].values).values      # datetime64[ns] ndarray
udates=np.sort(np.unique(dvals))
didx=np.searchsorted(udates,dvals)                   # exact: every dval is in udates
# hypothesis matrix: per-date mean edge per (signal, decile)
hyps=[]; cols=[]
for sname in ['mk63','skew63','jump5']:
    sv=TEc[sname].values; ok=np.isfinite(sv)
    dec=np.full(len(sv),-1)
    dec[ok]=pd.qcut(sv[ok],10,labels=False,duplicates='drop')
    for d in range(10):
        m5=dec==d
        col=np.full((len(udates),),np.nan)
        dfm=pd.DataFrame({'i':didx[m5],'e':edge[m5]}).groupby('i')['e'].mean()
        col[dfm.index.values]=dfm.values
        hyps.append(col); cols.append(f"{sname}_d{d+1}")
D=np.column_stack(hyps)   # n_dates x 30, NaN where a date has no obs in the cell
nT,K=D.shape
def tstats(M):
    mean=np.nanmean(M,axis=0); sd=np.nanstd(M,axis=0,ddof=1)
    cnt=np.sum(np.isfinite(M),axis=0)
    return mean/np.maximum(sd/np.sqrt(np.maximum(cnt,1)),1e-12)
t_obs=tstats(D)
lg("observed t range: %.2f .. %.2f  (n_dates %d)"%(np.min(t_obs),np.max(t_obs),nT))
mu_hat=np.nanmean(D,axis=0)
def run_rw(B,blk,seed):
    rng=np.random.default_rng(seed)
    Tboot=np.empty((B,K))
    for b in range(B):
        idx=[]; i=rng.integers(nT)
        while len(idx)<nT:
            ln=rng.geometric(1.0/blk); idx.extend(((i+np.arange(ln))%nT).tolist()); i=rng.integers(nT)
        Db=D[np.array(idx[:nT])]-mu_hat            # centered at observed means
        Tboot[b]=tstats(Db)
        if b%500==0: lg("  boot blk%d %d %.0fs"%(blk,b,time.time()-t0))
    order=np.argsort(-t_obs)
    adj=np.empty(K); prev=0.0
    for rank,k in enumerate(order):
        rem=order[rank:]
        maxb=np.nanmax(Tboot[:,rem],axis=1)
        pk=float(np.mean(maxb>=t_obs[k]))
        prev=max(prev,pk)
        adj[k]=prev
    return adj
adj10=run_rw(2000,10,11)
adj20=run_rw(1000,20,12)
res=sorted([(cols[k],round(float(t_obs[k]),2),round(float(adj10[k]),4),round(float(adj20[k]),4)) for k in range(K)],key=lambda x:x[2])
OUT={'note':'Romano-Wolf step-down FWER over the full 3-signal x 10-decile frontier grid; one-sided H1 edge>0; per-date mean edges; stationary bootstrap over dates. Primary blk=10 B=2000; sensitivity blk=20 B=1000. Tuple: (cell, t, adj_p_blk10, adj_p_blk20).',
     'n_dates':int(nT),'n_hypotheses':int(K),
     'survive_5pct_FWER_blk10':[r for r in res if r[2]<=0.05],
     'survive_5pct_FWER_blk20':[r for r in res if r[3]<=0.05],
     'all_adjusted':res}
json.dump(OUT,open(os.path.join(P,"romanowolf_results.json"),"w"),indent=2)
lg("ROMANOWOLFDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT['survive_5pct_FWER_blk10'],indent=1))
