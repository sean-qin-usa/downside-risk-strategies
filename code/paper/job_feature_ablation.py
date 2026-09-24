# job_feature_ablation.py -- does the frontier depend on the learner seeing score-like features?
# Same panel, split, GARCH filter and 11-level pooled boosted residual learner as job_composite.py
# (the Table 1 run). Three learners differ only in their state vector:
#   full      : logsig, zl1, absz5, zstd21, fracdn5      (the paper's learner)
#   nodisp    : logsig, zl1, fracdn5                     (no trailing residual-dispersion features)
#   scaleonly : logsig                                   (the GARCH scale alone)
# The score (mk63, |sk63|, jump5 and the composite) is computed as in the paper and is not a
# learner input in any variant. Reported: top-decile edge over GARCH-t by signal, the mk63 and
# composite decile profiles, and the overall edge, per learner, plus each reduced learner's loss
# against the full one in the top decile and overall.
# PREDICTIONS (2026-09-24, before the run): the top-decile edge survives every reduction. With
# logsig alone the top mk63-decile edge stays above half of the full learner's (i.e. > +1.5%,
# DM > 4) and deciles 1-8 stay within +-0.3%, because the post-shock scale correction that the
# decomposition attributes most of the edge to is a function of the scale state alone. Removing
# absz5 and zstd21 changes the top-decile edge by less than 0.5 points. If instead the edge
# collapses below +1% without the dispersion features, the frontier is partly the learner reading
# the score's own inputs, and the paper must say so.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=os.environ.get("GBC_PROJ",os.environ.get("GBC_PROJECT_DIR",r"C:\Users\OWNER\Claude\Projects\GBC Project")); t0=time.time(); lg=lambda s:print(s,flush=True)
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
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().abs().shift(1)
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=ZX+['mk63','skew63','jump5'])
    trn=dd[dd['idx']<cp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TRz.append(trn[ZX+['z']]); t2=tst.copy(); t2['permno']=pn; rows.append(t2)
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz)
lg("panel %d names %d rows %.0fs"%(TE.permno.nunique(),len(TE),time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
plG=np.zeros(len(Y))
for t in TAUS: plG+=pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t)
plG/=len(TAUS)
di,udates=pd.factorize(pd.to_datetime(TE['date'].values),sort=True); di=np.asarray(di)
def dec(x):
    r=np.full(len(x),-1); m=np.isfinite(x)
    r[m]=pd.qcut(pd.Series(x[m]),10,labels=False,duplicates='drop').values+1
    return r
def pct(x):
    r=np.full(len(x),np.nan); m=np.isfinite(x); r[m]=pd.Series(x[m]).rank(pct=True).values
    return r
mk=TE['mk63'].values; sk=TE['skew63'].values; jp=TE['jump5'].values
ok=np.isfinite(mk)&np.isfinite(sk)&np.isfinite(jp)
rk_mk,rk_sk,rk_jp=dec(mk),dec(sk),dec(jp)
comp_pct=np.where(ok, np.fmax.reduce([pct(mk),pct(sk),pct(jp)]), np.nan); cdec=dec(comp_pct)
VARIANTS={'full':ZX,'nodisp':['logsig','zl1','fracdn5'],'scaleonly':['logsig']}
def edge_of(d,base,mask):
    if mask.sum()<30: return None
    g=pd.DataFrame({'d':d[mask],'dt':di[mask]}).groupby('dt')['d'].mean()
    return {'edge_pct':round(100*float(d[mask].mean())/float(base[mask].mean()),3),'DM':nw_t(g.values),'n':int(mask.sum())}
OUT={'note':'Feature ablation of the Table 1 learner (see header). edge = (GARCH-t pinball - learner pinball)/GARCH-t pinball, 11 levels, per-date NW(10) DM. reduced_vs_full: (full pinball - reduced pinball)/full pinball, negative = reduced learner worse.',
     'n_rows':int(len(Y)),'n_names':int(TE.permno.nunique()),'variants':{}}
PL={}
for name,feats in VARIANTS.items():
    plE=np.zeros(len(Y))
    for t in TAUS:
        q=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06,random_state=0).fit(TRzc[feats].values,TRzc['z'].values).predict(TE[feats].values)
        plE+=pin(Y,MU+SIG*q,t)
    plE/=len(TAUS); PL[name]=plE; d=plG-plE
    OUT['variants'][name]={'features':feats,
        'top_decile':{'mk63':edge_of(d,plG,rk_mk==10),'skew63':edge_of(d,plG,rk_sk==10),'jump5':edge_of(d,plG,rk_jp==10),'composite':edge_of(d,plG,cdec==10)},
        'mk63_decile_profile':{int(k):edge_of(d,plG,rk_mk==k) for k in range(1,11)},
        'composite_decile_profile':{int(k):edge_of(d,plG,cdec==k) for k in range(1,11)},
        'overall':edge_of(d,plG,np.ones(len(Y),bool))}
    if name!='full':
        dd=PL['full']-plE
        OUT['variants'][name]['reduced_vs_full']={'top_mk63':edge_of(dd,PL['full'],rk_mk==10),'overall':edge_of(dd,PL['full'],np.ones(len(Y),bool))}
    lg("%s done %.0fs: top mk63 %s overall %s"%(name,time.time()-t0,OUT['variants'][name]['top_decile']['mk63'],OUT['variants'][name]['overall']))
    json.dump(OUT,open(os.path.join(P,"feature_ablation_results.json"),"w"),indent=2)
lg("ABLATIONDONE %.0fs"%(time.time()-t0))
