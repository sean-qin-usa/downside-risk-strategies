# Stage 1: read panel, subsample names, build features, cache arrays to the persistent mount.
import os, time, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
P="/sessions/gifted-sleepy-noether/mnt/GBC Project"; t0=time.time()
r=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),usecols=['permno','ret'],dtype={'permno':'int32','ret':'float32'})
print("read %.1fs rows=%d"%(time.time()-t0,len(r)),flush=True)
ch=pd.read_csv(os.path.join(P,"crsp_panel_chars.csv"))
rng=np.random.default_rng(11); names=r['permno'].unique(); rng.shuffle(names); names=names[:160]
r=r[r.permno.isin(names)].reset_index(drop=True); r['ret']=r['ret'].astype(float)*100.0
print("filtered %.1fs rows=%d names=%d"%(time.time()-t0,len(r),len(names)),flush=True)
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
print("feats %.1fs"%(time.time()-t0),flush=True)
ch['logmcap']=np.log(np.maximum(pd.to_numeric(ch['mcap_mm'],errors='coerce').fillna(300.0),1.0))
for c in ['sector','beta','annvol']: ch[c]=pd.to_numeric(ch[c],errors='coerce')
r=r.merge(ch[['permno','logmcap','sector','beta','annvol']],on='permno',how='left')
r['sector']=r['sector'].fillna(-1); r['beta']=r['beta'].fillna(1.0); r['annvol']=r['annvol'].fillna(0.3)
r['rv5']=r['rv5'].fillna(r['rv21']).fillna(2.0); r['rv21']=r['rv21'].fillna(2.0); r['mean21']=r['mean21'].fillna(0.0)
r=r.dropna(subset=['lag1']); r['abs1']=r['abs1'].fillna(r['abs1'].median())
XC=['lag1','abs1','rv5','rv21','mean21','dn','age','logmcap','sector','beta','annvol']
hold=set(names[:70]); tr=r[~r.permno.isin(hold)]; te=r[r.permno.isin(hold)]
if len(tr)>110000: tr=tr.sample(110000,random_state=1)
np.savez(os.path.join(P,"_gibbs_cache.npz"),
         Xtr=tr[XC].values.astype('float32'), ytr=tr['ret'].values.astype('float32'),
         Xte=te[XC].values.astype('float32'), yte=te['ret'].values.astype('float32'),
         age=te['age'].values.astype('float32'), own_mean=te['own_mean'].values.astype('float32'), own_std=te['own_std'].values.astype('float32'))
print("SAVED cache tr=%d te=%d %.1fs"%(len(tr),len(te),time.time()-t0),flush=True)
