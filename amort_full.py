# FULL-SCALE amortization validation (runs on ai2). Age-curve + feature ablation on the COMPLETE CRSP panel.
# Confirms the subsample findings: (1) amortized beats own-history at all ages; (2) own-recent dynamics (realized vol) carry the edge, not characteristics.
import os, json, time, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,t): e=y-q; return np.where(e>=0,t*e,(t-1)*e)
r=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),usecols=['permno','ret'],dtype={'permno':'int32','ret':'float32'})
ch=pd.read_csv(os.path.join(D,"crsp_panel_chars.csv"))
r['ret']=r['ret'].astype(float)*100.0
g=r.groupby('permno',sort=False); r['age']=g.cumcount()
r['lag1']=g['ret'].shift(1); r['abs1']=r['lag1'].abs()
r['rv5']=g['ret'].transform(lambda x:x.rolling(5,min_periods=3).std().shift(1))
r['rv21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).std().shift(1))
r['mean21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).mean().shift(1))
r['dn']=(r['lag1']<0).astype(float); r['ret2']=r['ret']**2
cs=g['ret'].cumsum()-r['ret']; cs2=g['ret2'].cumsum()-r['ret2']; cnt=r['age'].values.astype(float)
with np.errstate(invalid='ignore',divide='ignore'):
    om=np.where(cnt>0,cs/np.maximum(cnt,1),0.0); ov=np.where(cnt>1,cs2/np.maximum(cnt,1)-om**2,np.nan)
r['own_mean']=om; r['own_std']=np.sqrt(np.clip(ov,1e-6,None))
ch['logmcap']=np.log(np.maximum(pd.to_numeric(ch['mcap_mm'],errors='coerce').fillna(300.0),1.0))
for c in ['sector','beta','annvol']: ch[c]=pd.to_numeric(ch[c],errors='coerce')
r=r.merge(ch[['permno','logmcap','sector','beta','annvol']],on='permno',how='left')
r['sector']=r['sector'].fillna(-1); r['beta']=r['beta'].fillna(1.0); r['annvol']=r['annvol'].fillna(0.3)
r['rv5']=r['rv5'].fillna(r['rv21']).fillna(2.0); r['rv21']=r['rv21'].fillna(2.0); r['mean21']=r['mean21'].fillna(0.0)
r=r.dropna(subset=['lag1']); r['abs1']=r['abs1'].fillna(r['abs1'].median())
XC=['lag1','abs1','rv5','rv21','mean21','dn','age','logmcap','sector','beta','annvol']
rng=np.random.default_rng(11); names=r['permno'].unique(); rng.shuffle(names)
hold=set(names[:int(len(names)*0.4)]); tr=r[~r.permno.isin(hold)]; te=r[r.permno.isin(hold)].reset_index(drop=True)
lg("FULL panel: %d rows, %d names (%d held out); train=%d test=%d  %.0fs"%(len(r),len(names),len(hold),len(tr),len(te),time.time()-t0))
Xtr=tr[XC].values.astype('float32'); ytr=tr['ret'].values; Xte=te[XC].values.astype('float32')
AM={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=4,learning_rate=0.06,max_bins=128); m.fit(Xtr,ytr); AM[t]=m.predict(Xte)
lg("amortized full-model trained %.0fs"%(time.time()-t0))
y=te['ret'].values; age=te['age'].values.astype(float); ownm=te['own_mean'].values; owns=te['own_std'].values
tn={0.05:-1.645,0.10:-1.282,0.25:-0.674,0.50:0.0,0.75:0.674,0.90:1.282,0.95:1.645}
# (1) AGE-CURVE: amortized vs own-empirical(window) vs own-param
BUCK=[('d15_30',15,30),('d30_60',30,60),('d60_120',60,120),('d120_250',120,250),('d250_500',250,500),('d500_1000',500,1000),('d1000_2700',1000,2700)]
ownlist={pn:gg['ret'].values for pn,gg in te.groupby('permno')}
perm=te['permno'].values; pos={}; emp=np.full(len(te),np.nan)
# expanding empirical median-free: compute per-row empirical quantiles on last-500 window
curve={}
# vectorized-ish: for speed compute empirical via own_mean/own_std normal approx as 'param'; empirical done per bucket sample
def loss_rows(qf,mask): return float(np.mean([pin(y[mask],qf(t)[mask],t) for t in TAUS]))
qA=lambda t:AM[t]; qP=lambda t:ownm+np.clip(owns,1e-3,None)*tn[t]
for bn,lo,hi in BUCK:
    mask=(age>=lo)&(age<hi)&(age>=12)
    if mask.sum()<50: continue
    curve[bn]=dict(n=int(mask.sum()),amortized=round(loss_rows(qA,mask),4),own_param=round(loss_rows(qP,mask),4),
                   amort_vs_own=round(loss_rows(qA,mask)/loss_rows(qP,mask),4))
# (2) ABLATION on full data
SUB={'ALL':list(range(11)),'chars_only':[6,7,8,9,10],'own_recent_only':[0,1,2,3,4,5],
 'no_realized_vol':[0,1,4,5,6,7,8,9,10],'no_lags':[2,3,4,6,7,8,9,10],'no_chars':[0,1,2,3,4,5,6],'no_age':[0,1,2,3,4,5,7,8,9,10]}
abl={}
T3=[0.05,0.5,0.95]
for nm,cols in SUB.items():
    tot=0.0
    for t in T3:
        m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=150,max_depth=4,learning_rate=0.07,max_bins=128); m.fit(Xtr[:,cols],ytr); tot+=np.mean(pin(y,m.predict(Xte[:,cols]),t))
    abl[nm]=round(float(tot/len(T3)),4)
base=abl['ALL']; ablr={k:{'pinball':v,'pct_vs_ALL':round((v/base-1)*100,1)} for k,v in sorted(abl.items(),key=lambda x:x[1])}
out={'note':'FULL-SCALE amortization validation on complete CRSP panel (run on ai2). Age-curve (amortized vs own-parametric by listing age) + feature ablation.','n_rows':int(len(r)),'n_names':int(len(names)),'n_holdout':len(hold),
 'age_curve':curve,'ablation_ALL_pinball':base,'ablation':ablr}
json.dump(out,open(os.path.join(D,"amort_full_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
