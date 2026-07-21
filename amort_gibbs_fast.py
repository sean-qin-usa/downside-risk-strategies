# Fast in-sandbox Gibbs/amortized-as-prior test - trimmed to finish under the call limit.
import json, os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
P="/sessions/gifted-sleepy-noether/mnt/GBC Project"; t0=time.time()
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
r=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),usecols=['permno','ret'],dtype={'permno':'int32','ret':'float32'})  # file is pre-sorted by permno,date
ch=pd.read_csv(os.path.join(P,"crsp_panel_chars.csv"))
rng=np.random.default_rng(11); names=r['permno'].unique(); rng.shuffle(names); names=names[:140]
r=r[r.permno.isin(names)].reset_index(drop=True); r['ret']=r['ret'].astype(float)*100.0
g=r.groupby('permno',sort=False)
r['age']=g.cumcount()
r['lag1']=g['ret'].shift(1); r['abs1']=r['lag1'].abs()
r['rv5']=g['ret'].transform(lambda x:x.rolling(5,min_periods=3).std().shift(1))
r['rv21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).std().shift(1))
r['mean21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).mean().shift(1))
r['dn']=(r['lag1']<0).astype(float); r['ret2']=r['ret']**2
csum=g['ret'].cumsum()-r['ret']; csum2=g['ret2'].cumsum()-r['ret2']; cnt=r['age'].values.astype(float)
with np.errstate(invalid='ignore',divide='ignore'):
    om=np.where(cnt>0,csum/np.maximum(cnt,1),0.0); ov=np.where(cnt>1,csum2/np.maximum(cnt,1)-om**2,np.nan)
r['own_mean']=om; r['own_std']=np.sqrt(np.clip(ov,1e-6,None))
ch['logmcap']=np.log(np.maximum(pd.to_numeric(ch['mcap_mm'],errors='coerce').fillna(300.0),1.0))
for c in ['sector','beta','annvol']: ch[c]=pd.to_numeric(ch[c],errors='coerce')
r=r.merge(ch[['permno','logmcap','sector','beta','annvol']],on='permno',how='left')
r['sector']=r['sector'].fillna(-1); r['beta']=r['beta'].fillna(1.0); r['annvol']=r['annvol'].fillna(0.3)
r['rv5']=r['rv5'].fillna(r['rv21']).fillna(2.0); r['rv21']=r['rv21'].fillna(2.0); r['mean21']=r['mean21'].fillna(0.0)
r=r.dropna(subset=['lag1']); r['abs1']=r['abs1'].fillna(r['abs1'].median())
XC=['lag1','abs1','rv5','rv21','mean21','dn','age','logmcap','sector','beta','annvol']
hold=set(names[:60]); tr=r[~r.permno.isin(hold)]; te=r[r.permno.isin(hold)].reset_index(drop=True)
if len(tr)>90000: tr=tr.sample(90000,random_state=1)
print("train %d hold %d feat %.0fs"%(len(tr),len(te),time.time()-t0),flush=True)
Xtr=tr[XC].values.astype('float32'); ytr=tr['ret'].values; Xte=te[XC].values.astype('float32')
AM={}
for tau in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=tau,max_iter=45,max_depth=3,learning_rate=0.1,max_bins=48)
    m.fit(Xtr,ytr); AM[tau]=m.predict(Xte)
print("models %.0fs"%(time.time()-t0),flush=True)
med=AM[0.50]; astd=np.maximum((AM[0.90]-AM[0.10])/2.563,1e-3)
y=te['ret'].values; age=te['age'].values.astype(float); om=te['own_mean'].values; os_=te['own_std'].values
K=80.0; w=age/(age+K); b=1.0+w*(np.clip(os_,1e-3,None)/astd-1.0); a=w*(om-med)
tn={0.05:-1.645,0.10:-1.282,0.25:-0.674,0.50:0.0,0.75:0.674,0.90:1.282,0.95:1.645}
BUCK=[('d15_30',15,30),('d30_60',30,60),('d60_120',60,120),('d120_250',120,250),('d250_500',250,500),('d500_1000',500,1000),('d1000_2700',1000,2700)]
qA=lambda t:AM[t]; qG=lambda t:med+a+b*(AM[t]-med); qO=lambda t:om+np.clip(os_,1e-3,None)*tn[t]
def loss(qf,m): return float(np.mean([pin(y[m],qf(t)[m],t) for t in TAUS]))
res={'note':'Amortized-as-prior (Gibbs): q=amort_med+a+b*(amort_q-amort_med); a,b shrink to prior(0,1) w=age/(age+80). Subsampled(140 names) in-sandbox CRSP run.','K':K,'n_train':int(len(tr)),'curve':{}}
for bn,lo,hi in BUCK:
    m=(age>=lo)&(age<hi)&(age>=12)
    if m.sum()<40: continue
    am=loss(qA,m); gb=loss(qG,m); ow=loss(qO,m)
    res['curve'][bn]=dict(n=int(m.sum()),amortized=round(am,4),gibbs_prior=round(gb,4),own_parametric=round(ow,4),gibbs_vs_amort=round(gb/am,4),gibbs_improves=bool(gb<am))
json.dump(res,open(os.path.join(P,"amort_gibbs.json"),"w"),indent=2,default=str)
print("DONE %.0fs"%(time.time()-t0),flush=True)
for k,v in res['curve'].items(): print(k,'amort',v['amortized'],'GIBBS',v['gibbs_prior'],'g/a',v['gibbs_vs_amort'],v['gibbs_improves'],flush=True)
