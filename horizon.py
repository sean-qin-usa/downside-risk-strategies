# HORIZON STUDY (ai2): does the nonparametric (GBM) edge over GARCH grow with forecast horizon? h-day-ahead cumulative-return quantiles.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]; HORIZONS=[1,5,10,20]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
r=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),usecols=['permno','ret'],dtype={'permno':'int32','ret':'float32'})
ch=pd.read_csv(os.path.join(D,"crsp_panel_chars.csv")); r['ret']=r['ret'].astype(float)*100.0
g=r.groupby('permno',sort=False); r['age']=g.cumcount()
r['lag1']=g['ret'].shift(1); r['abs1']=r['lag1'].abs()
r['rv5']=g['ret'].transform(lambda x:x.rolling(5,min_periods=3).std().shift(1))
r['rv21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).std().shift(1))
r['mean21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).mean().shift(1)); r['dn']=(r['lag1']<0).astype(float)
# forward cumulative returns for each horizon (target)
for h in HORIZONS:
    r['fwd%d'%h]=g['ret'].transform(lambda x:x[::-1].rolling(h,min_periods=h).sum()[::-1]).shift(-0) if False else g['ret'].transform(lambda x:x.rolling(h,min_periods=h).sum().shift(-h))
ch['logmcap']=np.log(np.maximum(pd.to_numeric(ch['mcap_mm'],errors='coerce').fillna(300.0),1.0))
for c in ['sector','beta','annvol']: ch[c]=pd.to_numeric(ch[c],errors='coerce')
r=r.merge(ch[['permno','logmcap','sector','beta','annvol']],on='permno',how='left')
r['sector']=r['sector'].fillna(-1); r['beta']=r['beta'].fillna(1.0); r['annvol']=r['annvol'].fillna(0.3)
r['rv5']=r['rv5'].fillna(r['rv21']).fillna(2.0); r['rv21']=r['rv21'].fillna(2.0); r['mean21']=r['mean21'].fillna(0.0)
r=r.dropna(subset=['lag1','rv21']); r['abs1']=r['abs1'].fillna(r['abs1'].median())
XC=['lag1','abs1','rv5','rv21','mean21','dn','age','logmcap','sector','beta','annvol']
rng=np.random.default_rng(11); names=r['permno'].unique(); rng.shuffle(names); hold=set(names[:int(len(names)*0.4)])
tn={t:stats.norm.ppf(t) for t in TAUS}
out={'note':'Horizon study (ai2): amortized GBM-quantile vs GARCH-style scaling for h-day-ahead CUMULATIVE return quantiles. GBM learns h-day quantiles directly; GARCH baseline = mu*h + sqrt(h)*sig_t * t-quantile (per-name GARCH-t current sigma). ratio=gbm/garch avg pinball (<1=nonparam better). Thesis: edge grows with horizon (fat tails compound).','by_horizon':{}}
from arch import arch_model
for h in HORIZONS:
    tgt='fwd%d'%h; dd=r.dropna(subset=[tgt])
    tr=dd[~dd.permno.isin(hold)]; te=dd[dd.permno.isin(hold)]
    gbm={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=180,max_depth=4,learning_rate=0.06).fit(tr[XC].values,tr[tgt].values) for t in TAUS}
    lg("h=%d GBM trained %.0fs"%(h,time.time()-t0))
    gl=nl=0.0; cnt=0
    for pn in [p for p in names if p in hold]:
        d=te[te.permno==pn]
        if len(d)<120: continue
        y=d[tgt].values; dr=d['ret'].values
        try:
            res=arch_model(dr,vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
            p=res.params; nu=float(p.get('nu',8)); mu=float(p.get('mu',0)); cv=float(res.conditional_volatility[-len(y):].mean())
        except Exception: continue
        sig_h=cv*math.sqrt(h); mu_h=mu*h; tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
        Xp={t:gbm[t].predict(d[XC].values) for t in TAUS}
        for j in range(len(y)):
            yi=y[j]
            gl+=np.mean([pin(yi,mu_h+sig_h*stats.t.ppf(t,nu)/tsc,t) for t in TAUS]); nl+=np.mean([pin(yi,Xp[t][j],t) for t in TAUS]); cnt+=1
        if cnt>200000: break
    out['by_horizon']['h%d'%h]=dict(n=cnt,garch=round(gl/cnt,4),gbm=round(nl/cnt,4),ratio=round(nl/gl,4))
    lg("h=%d ratio %s %.0fs"%(h,out['by_horizon']['h%d'%h]['ratio'],time.time()-t0))
    json.dump(out,open(os.path.join(D,"horizon_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out['by_horizon'],indent=2))
