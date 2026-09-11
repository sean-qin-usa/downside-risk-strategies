# job_mechanism.py -- MECHANISM IDENTIFICATION [R19 #1].
# Reviewer: the tv-relative score has Spearman 0.971 with raw kurtosis and 82.5% top-decile
# overlap, so "the score reads departure from the fitted law, not raw tail mass" is not
# established -- the same observations do the work. This job runs DISCRIMINATING tests, not
# another robustness re-sort:
#   (1) rho(raw,nurel) + top-decile overlap (reproduce the reviewer's numbers)
#   (2) univariate top-decile edge: raw mk63 vs nu-relative percentile
#   (3) double-sort raw-kurt quintile (rows) x fitted-nu quintile (cols): does nu matter
#       HOLDING raw kurtosis ~fixed? (low nu = raw kurt expected; high nu = raw kurt surprising)
#   (4) discordant deciles: top under one measure but not the other -- which wins in disagreement?
#   (5) Fama-MacBeth cross-sectional incremental betas of z(raw) and z(nurel) on the per-obs edge.
# Null/percentile code copied verbatim from job_nurel.py so the null estimator matches the
# observed pandas .kurt(). Engine/panel identical to job_causal_frontier / job_fz_fullpanel.
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
def pin(y,q,t): dd=y-q; return np.where(dd>=0,t*dd,(t-1)*dd)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    dm=x-x.mean(); v=np.mean(dm*dm)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(dm[k:]*dm[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
# ---- nu-relative null (verbatim from job_nurel.py) ----
def g2_excess_kurt(X):
    n=X.shape[1]; xb=X.mean(axis=1,keepdims=True); dv=X-xb
    m2=(dv**2).sum(axis=1); m4=(dv**4).sum(axis=1); s2=m2/(n-1)
    return (n*(n+1)/((n-1)*(n-2)*(n-3)))*(m4/np.maximum(s2**2,1e-300))-3*(n-1)**2/((n-2)*(n-3))
rng=np.random.default_rng(7)
NUGRID=np.array([2.6,2.8,3.0,3.2,3.4,3.6,3.8,4.0,4.3,4.6,5.0,5.5,6.0,7.0,8.0,10.0,12.0,15.0,20.0,30.0,50.0])
S=4000; W=63; NULLS={}
for nug in NUGRID:
    draws=rng.standard_t(nug,size=(S,W)); NULLS[nug]=np.sort(g2_excess_kurt(draws))
def pctile(mk,nu):
    nu=min(max(nu,NUGRID[0]),NUGRID[-1]); i=int(np.searchsorted(NUGRID,nu)); i=min(max(i,1),len(NUGRID)-1)
    lo,hi=NUGRID[i-1],NUGRID[i]; w=(nu-lo)/(hi-lo) if hi>lo else 0.0
    p_lo=np.searchsorted(NULLS[lo],mk)/S; p_hi=np.searchsorted(NULLS[hi],mk)/S
    return (1-w)*p_lo+w*p_hi
lg("null tables built %.0fs"%(time.time()-t0))
# ---- panel ----
TRz=[]; rows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        pp=r1.params; om,al,be,mu=float(pp['omega']),float(pp['alpha[1]']),float(pp['beta[1]']),float(pp.get('mu',0)); nu=float(pp.get('nu',8))
    except Exception: continue
    e0=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e0[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); zz=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':zz,'date':dts})
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
    ZQ[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06,random_state=0).fit(TRzc[ZX].values,TRzc['z'].values).predict(TE[ZX].values)
    lg("  tau %.3f %.0fs"%(t,time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
plE=np.zeros(len(Y)); plG=np.zeros(len(Y))
for t in TAUS:
    plE+=pin(Y,MU+SIG*ZQ[t],t); plG+=pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t)
plE/=len(TAUS); plG/=len(TAUS)
d=plG-plE; raw=TE['mk63'].values; nuv=NU
nurel=np.array([pctile(m,nn) for m,nn in zip(raw,nuv)])
di,udates=pd.factorize(pd.to_datetime(TE['date'].values),sort=True); di=np.asarray(di)
ok=np.isfinite(raw)&np.isfinite(nurel)&np.isfinite(d)
raw_=raw[ok]; nurel_=nurel[ok]; d_=d[ok]; di_=di[ok]; nu_=nuv[ok]; plG_=plG[ok]
def zsc(x): return (x-np.mean(x))/np.std(x)
zr=zsc(raw_); zn=zsc(nurel_)
rho=round(float(stats.spearmanr(raw_,nurel_).statistic),3)
thr_r=np.quantile(raw_,0.9); thr_n=np.quantile(nurel_,0.9)
topr=raw_>=thr_r; topn=nurel_>=thr_n
overlap=round(float(np.mean(topr&topn)/0.1),3)
def edge(mask):
    if mask.sum()<30: return None
    g=pd.DataFrame({'d':d_[mask],'dt':di_[mask]}).groupby('dt')['d'].mean()
    return {'edge_pct':round(100*float(d_[mask].mean())/float(plG_[mask].mean()),3),'DM':nw_t(g.values),'n':int(mask.sum())}
res_raw=edge(topr); res_nurel=edge(topn)
# (3) double-sort raw-kurt quintile (rows) x fitted-nu quintile (cols)
rq=pd.qcut(pd.Series(raw_),5,labels=False,duplicates='drop').values
nq=pd.qcut(pd.Series(nu_),5,labels=False,duplicates='drop').values
ds=[[None]*5 for _ in range(5)]
for i in range(5):
    for j in range(5):
        m=(rq==i)&(nq==j)
        if m.sum()>=30: ds[i][j]=round(100*float(d_[m].mean())/float(plG_[m].mean()),2)
byNU_in_topraw={int(j):edge((rq==4)&(nq==j)) for j in range(5)}
# (4) discordant deciles
disc_n_not_r=edge(topn&(~topr)); disc_r_not_n=edge(topr&(~topn))
# (5) Fama-MacBeth incremental betas (within-date cross-sectional OLS)
bR=[]; bN=[]
for dd0 in np.unique(di_):
    m=di_==dd0
    if m.sum()<40: continue
    rr2=zr[m]-zr[m].mean(); nn2=zn[m]-zn[m].mean()
    X=np.column_stack([np.ones(m.sum()),rr2,nn2])
    try: b=np.linalg.lstsq(X,d_[m],rcond=None)[0]
    except Exception: continue
    bR.append(b[1]); bN.append(b[2])
fm={'beta_raw_mean':round(float(np.mean(bR)),5),'t_raw':nw_t(np.array(bR)),
    'beta_nurel_mean':round(float(np.mean(bN)),5),'t_nurel':nw_t(np.array(bN)),'n_dates':len(bR)}
OUT={'note':('Mechanism identification [R19#1]. Fama-MacBeth: within-date cross-sectional OLS of the '
  'per-obs GARCH-minus-engine 11-tau pinball edge on within-date-demeaned z(raw mk63) and '
  'z(nu-relative pctile); betas averaged, NW(10) t across dates. t_nurel is the incremental content '
  'of the nu-relative score HOLDING raw kurtosis fixed (and t_raw vice versa). Double-sort: edge% by '
  'raw-kurt quintile (rows 0=low..4=high) x fitted-nu quintile (cols 0=low..4=high). Discordant: '
  'top-decile under one measure but not the other. If neither has robust incremental content, the two '
  'measures are empirically the same object and no mechanism can be separated from the frontier.'),
 'n_rows':int(ok.sum()),'n_names':int(TE.permno.nunique()),
 'spearman_raw_nurel':rho,'topdecile_overlap':overlap,
 'edge_top_raw':res_raw,'edge_top_nurel':res_nurel,
 'famamacbeth_incremental':fm,
 'doublesort_rawQ_rows_x_nuQ_cols':ds,
 'edge_by_nuQ_within_top_raw_quintile':byNU_in_topraw,
 'discordant_topnurel_not_topraw':disc_n_not_r,'discordant_topraw_not_topnurel':disc_r_not_n}
json.dump(OUT,open(os.path.join(P,"mechanism_results.json"),"w"),indent=2)
lg("MECHANISMDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1))
