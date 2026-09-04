# EDGE CONCENTRATION BY VOL REGIME (ai2): does the nonparametric (GBM-quantile) edge over GARCH-t concentrate in high-volatility states?
# Amortized GBM vs per-name GARCH-t, day-by-day pinball, bucketed by that day's recent realized-vol quintile.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
r=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),usecols=['permno','ret'],dtype={'permno':'int32','ret':'float32'})
ch=pd.read_csv(os.path.join(D,"crsp_panel_chars.csv")); r['ret']=r['ret'].astype(float)*100.0
g=r.groupby('permno',sort=False); r['age']=g.cumcount()
r['lag1']=g['ret'].shift(1); r['abs1']=r['lag1'].abs()
r['rv5']=g['ret'].transform(lambda x:x.rolling(5,min_periods=3).std().shift(1))
r['rv21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).std().shift(1))
r['mean21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).mean().shift(1))
r['dn']=(r['lag1']<0).astype(float)
ch['logmcap']=np.log(np.maximum(pd.to_numeric(ch['mcap_mm'],errors='coerce').fillna(300.0),1.0))
for c in ['sector','beta','annvol']: ch[c]=pd.to_numeric(ch[c],errors='coerce')
r=r.merge(ch[['permno','logmcap','sector','beta','annvol']],on='permno',how='left')
r['sector']=r['sector'].fillna(-1); r['beta']=r['beta'].fillna(1.0); r['annvol']=r['annvol'].fillna(0.3)
r['rv5']=r['rv5'].fillna(r['rv21']).fillna(2.0); r['rv21']=r['rv21'].fillna(2.0); r['mean21']=r['mean21'].fillna(0.0)
r=r.dropna(subset=['lag1','rv21']); r['abs1']=r['abs1'].fillna(r['abs1'].median())
XC=['lag1','abs1','rv5','rv21','mean21','dn','age','logmcap','sector','beta','annvol']
rng=np.random.default_rng(11); names=r['permno'].unique(); rng.shuffle(names); hold=set(names[:int(len(names)*0.4)])
tr=r[~r.permno.isin(hold)]
AM={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=200,max_depth=4,learning_rate=0.06); m.fit(tr[XC].values,tr['ret'].values); AM[t]=m
lg("amortized GBM trained %.0fs"%(time.time()-t0))
from arch import arch_model
rows=[]  # (rv21, garch_pin, gbm_pin)
holdnames=[pn for pn in names if pn in hold]
done=0
for pn in holdnames:
    d=r[r.permno==pn]
    if len(d)<500: continue
    y=d['ret'].values; n=len(d); sp=int(n*0.6)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: continue
    e=y[:sp]-mu; s2=np.empty(len(e)); s2[0]=e.var()
    for k in range(1,len(e)): s2[k]=om+al*e[k-1]**2+be*s2[k-1]
    sig2=s2[-1]; tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    X=d[XC].values; rv=d['rv21'].values
    gpred={t:AM[t].predict(X[sp:]) for t in TAUS}
    for j,i in enumerate(range(sp,n)):
        sig2=om+al*(y[i-1]-mu)**2+be*sig2; sig=math.sqrt(max(sig2,1e-9)); yi=y[i]
        gp=np.mean([pin(yi,mu+sig*stats.t.ppf(t,nu)/tsc,t) for t in TAUS])
        np_=np.mean([pin(yi,gpred[t][j],t) for t in TAUS])
        rows.append((rv[i],gp,np_))
    done+=1
    if done%20==0: lg("processed %d names, %d test-days %.0fs"%(done,len(rows),time.time()-t0))
A=np.array(rows); rvv=A[:,0]; gp=A[:,1]; npv=A[:,2]
qs=np.quantile(rvv,[0.2,0.4,0.6,0.8])
out={'note':'Edge concentration by recent-vol (rv21) quintile: amortized GBM-quantile vs per-name GARCH-t, held-out CRSP names, per test-day pinball. edge = garch_pinball - gbm_pinball (>0 = nonparam better). Thesis: edge grows with vol quintile.','n_names':int(done),'n_testdays':int(len(A)),'by_vol_quintile':{}}
lab=['Q1_calm','Q2','Q3','Q4','Q5_turbulent']
idx=np.digitize(rvv,qs)
for qi in range(5):
    m=idx==qi
    if m.sum()<100: continue
    out['by_vol_quintile'][lab[qi]]=dict(n=int(m.sum()),rv21_range=[round(float(rvv[m].min()),2),round(float(rvv[m].max()),2)],garch_pinball=round(float(gp[m].mean()),4),gbm_pinball=round(float(npv[m].mean()),4),edge_garch_minus_gbm=round(float((gp[m]-npv[m]).mean()),4),ratio_np_over_garch=round(float(npv[m].mean()/gp[m].mean()),4))
json.dump(out,open(os.path.join(D,"edge_regime_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
