# M5-Uncertainty Stage 1: subsample series, melt, merge calendar, build features, cache.
import os, time, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
M="/sessions/gifted-sleepy-noether/mnt/GBC Project/competitions/m5"; t0=time.time()
NSER=1200; HIST=460; HTEST=28
cal=pd.read_csv(os.path.join(M,"calendar.csv"))
cal['event']=cal['event_name_1'].notna().astype(int)
calmap=cal.set_index('d')[['wday','month','snap_CA','snap_TX','snap_WI','event']]
sv=pd.read_csv(os.path.join(M,"sales_train_evaluation.csv"))
rng=np.random.default_rng(7); sv=sv.iloc[rng.permutation(len(sv))[:NSER]].reset_index(drop=True)
idc=['id','item_id','dept_id','cat_id','store_id','state_id']
daycols=[c for c in sv.columns if c.startswith('d_')]
keep=daycols[-HIST:]
long=sv[idc+keep].melt(id_vars=idc,var_name='d',value_name='sales')
long['dnum']=long['d'].str.slice(2).astype(int)
long=long.sort_values(['id','dnum']).reset_index(drop=True)
# calendar features
long=long.merge(calmap,left_on='d',right_index=True,how='left')
st=long['state_id'].values
long['snap']=np.where(st=='CA',long['snap_CA'],np.where(st=='TX',long['snap_TX'],long['snap_WI']))
g=long.groupby('id',sort=False)['sales']
long['lag7']=g.shift(7); long['lag28']=g.shift(28)
long['rmean7']=g.shift(1).rolling(7,min_periods=3).mean().reset_index(0,drop=True)
long['rmean28']=g.shift(1).rolling(28,min_periods=10).mean().reset_index(0,drop=True)
long['rmean56']=g.shift(1).rolling(56,min_periods=20).mean().reset_index(0,drop=True)
for c in ['dept_id','cat_id','store_id','state_id']:
    long[c+'_e']=long[c].astype('category').cat.codes
CANDIDATE=['lag7','lag28','rmean7','rmean28','rmean56','wday','month','snap','event','dept_id_e','cat_id_e','store_id_e','state_id_e']
long=long.dropna(subset=['lag28','rmean28'])
dmax=long['dnum'].max(); test_lo=dmax-HTEST+1
tr=long[long['dnum']<test_lo]; te=long[long['dnum']>=test_lo]
# per-series naive scale (mean abs 1-step diff on training portion)
def scale_of(s): d=np.abs(np.diff(s.values)); return d.mean() if len(d) and d.mean()>0 else 1.0
sc=tr.groupby('id')['sales'].apply(scale_of)
te=te.merge(sc.rename('scale'),left_on='id',right_index=True,how='left')
np.savez(os.path.join(M,"_m5_cache.npz"),
         Xtr=tr[CANDIDATE].values.astype('float32'), ytr=tr['sales'].values.astype('float32'),
         Xte=te[CANDIDATE].values.astype('float32'), yte=te['sales'].values.astype('float32'),
         scale=te['scale'].values.astype('float32'), feat=np.array(CANDIDATE))
print("SAVED tr=%d te=%d nser=%d %.1fs"%(len(tr),len(te),NSER,time.time()-t0),flush=True)
