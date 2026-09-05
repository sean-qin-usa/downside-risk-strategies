# job_nurel.py -- IS mk63 A MODEL-RELATIVE MISSPECIFICATION SCORE? (wave 9, v2)
# v2: null grid extended below nu=4 (down to 2.6) so names with heavy fitted tails are
# normalized against their own null rather than clipped -- the panel's median fitted nu
# is ~3.9, below the population-kurtosis existence boundary, which is exactly why the
# normalization must use the simulated finite-window null, not kappa(nu)=6/(nu-4).
# The objection: raw trailing excess kurtosis mixes (a) correctly predicted heavy tails
# under each name's fitted t_nu (a t_5 SHOULD show kurtosis ~6) with (b) genuine local
# departure from the fitted innovation law. If the frontier is only (a), "misspecification
# score" is the wrong name. The decisive test: convert each observation's mk63 into a
# percentile against the NULL distribution of 63-window sample excess kurtosis under that
# name's own fitted t_{nu_i}, and re-sort the frontier by the nu-relative percentile.
# If the top-decile edge survives, the score is model-relative, not just tail-mass.
# Same audit panel and engine construction as job_fz_fullpanel (200 names, GARCH y[:sp],
# pooled GBM on trn z, 11-level average pinball); edge = (garch - engine)/garch.
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
def g2_excess_kurt(X):
    # pandas .kurt() formula (unbiased G2), rows = windows
    n=X.shape[1]; xb=X.mean(axis=1,keepdims=True); d=X-xb
    m2=(d**2).sum(axis=1); m4=(d**4).sum(axis=1)
    s2=m2/(n-1)
    return (n*(n+1)/((n-1)*(n-2)*(n-3)))*(m4/np.maximum(s2**2,1e-300))-3*(n-1)**2/((n-2)*(n-3))
# ---- null distributions of 63-window sample excess kurtosis under standardized t_nu ----
rng=np.random.default_rng(7)
NUGRID=np.array([2.6,2.8,3.0,3.2,3.4,3.6,3.8,4.0,4.3,4.6,5.0,5.5,6.0,7.0,8.0,10.0,12.0,15.0,20.0,30.0,50.0])
S=4000; W=63
NULLS={}
for nug in NUGRID:
    draws=rng.standard_t(nug,size=(S,W))
    K=g2_excess_kurt(draws)                    # scale-invariant, no need to standardize
    NULLS[nug]=np.sort(K)
lg("null tables built %.0fs"%(time.time()-t0))
def pctile(mk,nu):
    nu=min(max(nu,NUGRID[0]),NUGRID[-1])
    i=int(np.searchsorted(NUGRID,nu)); i=min(max(i,1),len(NUGRID)-1)
    lo,hi=NUGRID[i-1],NUGRID[i]; w=(nu-lo)/(hi-lo) if hi>lo else 0.0
    p_lo=np.searchsorted(NULLS[lo],mk)/S; p_hi=np.searchsorted(NULLS[hi],mk)/S
    return (1-w)*p_lo+w*p_hi
# ---- panel ----
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
    dd=df.dropna(subset=ZX)
    trn=dd[dd['idx']<cp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TRz.append(trn[ZX+['z']]); t2=tst.copy(); t2['permno']=pn; rows.append(t2)
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz)
lg("panel %d names %d test rows %.0fs"%(TE.permno.nunique(),len(TE),time.time()-t0))
ZQ={}
for t in TAUS:
    ZQ[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values).predict(TE[ZX].values)
    lg("  tau %.3f %.0fs"%(t,time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
plE=np.zeros(len(Y)); plG=np.zeros(len(Y))
for t in TAUS:
    plE+=pin(Y,MU+SIG*ZQ[t],t)
    plG+=pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t)
plE/=len(TAUS); plG/=len(TAUS)
d=plG-plE; dates=TE['date'].values
mkv=TE['mk63'].values
pct=np.array([pctile(m,nu) for m,nu in zip(mkv,NU)])
def decile_report(score):
    ok=np.isfinite(score)
    q=pd.qcut(pd.Series(score[ok]),10,labels=False,duplicates='drop')
    out=[]
    top=None
    for dec in range(int(q.max())+1):
        m=np.zeros(len(Y),bool); m[np.where(ok)[0][q.values==dec]]=True
        edge=100*float(d[m].mean())/float(plG[m].mean())
        dd_=pd.DataFrame({'d':d[m],'date':dates[m]}).groupby('date')['d'].mean()
        r={'decile':dec+1,'edge_pct':round(edge,3),'DM':nw_t(dd_.values),'n':int(m.sum())}
        out.append(r); top=r
    return out,top
rep_raw,top_raw=decile_report(mkv)
rep_nrm,top_nrm=decile_report(pct)
ok=np.isfinite(mkv)&np.isfinite(pct)
from scipy.stats import spearmanr
_sr=spearmanr(mkv[ok],pct[ok]); rho=float(_sr[0])
thr_r=np.nanquantile(mkv[ok],0.9); thr_n=np.nanquantile(pct[ok],0.9)
overlap=float(np.mean((mkv[ok]>=thr_r)&(pct[ok]>=thr_n))/0.1)
OUT={'note':('nu-relative misspecification score test: mk63 converted to a percentile against the '
  'simulated null of 63-window sample excess kurtosis (pandas G2 estimator) under each name\'s fitted '
  't_nu (grid interpolation, 4000 sims per grid point, nu grid spans [2.6,50] so no fitted nu in this panel is clipped from below; the finite-window null is well defined for every nu even where population kurtosis is not). Frontier deciles '
  're-sorted by the percentile; edge = (garch-engine)/garch avg 11-level pinball, per-date DM NW(10). '
  'If the top decile survives, the score is model-relative rather than raw tail mass.'),
 'nu_summary':{'min':round(float(np.min(NU)),2),'p25':round(float(np.percentile(NU,25)),2),
   'median':round(float(np.median(NU)),2),'p75':round(float(np.percentile(NU,75)),2),'max':round(float(np.max(NU)),2)},
 'overall_edge_pct':round(100*float(d.mean())/float(plG.mean()),3),
 'raw_mk63':{'deciles':rep_raw,'top':top_raw},
 'nu_relative':{'deciles':rep_nrm,'top':top_nrm},
 'spearman_raw_vs_percentile':round(rho,3),
 'top_decile_overlap_frac':round(overlap,3)}
json.dump(OUT,open(os.path.join(P,"nurel_results.json"),"w"),indent=2)
lg("NURELDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1)[:2400])
