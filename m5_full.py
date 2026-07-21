# M5-Uncertainty improved: + sell_prices feature + more series. Runs on ai2. Level-12 scaled pinball loss (SPL).
import os, json, time, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
M=os.path.expanduser("~/sean_dev/GBC_data/m5"); t0=time.time(); lg=lambda s:print(s,flush=True)
NSER=8000; HIST=520; HTEST=28
TAUS=[0.005,0.025,0.165,0.25,0.5,0.75,0.835,0.975,0.995]
def pin(y,q,t): e=y-q; return np.where(e>=0,t*e,(t-1)*e)
cal=pd.read_csv(os.path.join(M,"calendar.csv"))
cal['event']=cal['event_name_1'].notna().astype(int)
calmap=cal.set_index('d')[['wm_yr_wk','wday','month','snap_CA','snap_TX','snap_WI','event']]
sv=pd.read_csv(os.path.join(M,"sales_train_evaluation.csv"))
rng=np.random.default_rng(7); sv=sv.iloc[rng.permutation(len(sv))[:NSER]].reset_index(drop=True)
idc=['id','item_id','dept_id','cat_id','store_id','state_id']; daycols=[c for c in sv.columns if c.startswith('d_')]; keep=daycols[-HIST:]
long=sv[idc+keep].melt(id_vars=idc,var_name='d',value_name='sales'); long['dnum']=long['d'].str.slice(2).astype(int)
long=long.sort_values(['id','dnum']).reset_index(drop=True)
long=long.merge(calmap,left_on='d',right_index=True,how='left')
st=long['state_id'].values; long['snap']=np.where(st=='CA',long['snap_CA'],np.where(st=='TX',long['snap_TX'],long['snap_WI']))
lg("melted %d rows %.0fs; merging prices"%(len(long),time.time()-t0))
# sell_prices merge (filter to sampled store/item first)
sp=pd.read_csv(os.path.join(M,"sell_prices.csv"))
keyset=set(zip(sv['store_id'],sv['item_id'])); sp=sp[[ (a,b) in keyset for a,b in zip(sp['store_id'],sp['item_id']) ]]
long=long.merge(sp,on=['store_id','item_id','wm_yr_wk'],how='left')
g=long.groupby('id',sort=False)
long['lag7']=g['sales'].shift(7); long['lag28']=g['sales'].shift(28)
long['rmean7']=g['sales'].shift(1).rolling(7,min_periods=3).mean().reset_index(0,drop=True)
long['rmean28']=g['sales'].shift(1).rolling(28,min_periods=10).mean().reset_index(0,drop=True)
long['rmean56']=g['sales'].shift(1).rolling(56,min_periods=20).mean().reset_index(0,drop=True)
long['price']=long['sell_price']
long['price_rel']=long['sell_price']/g['sell_price'].transform(lambda x:x.rolling(8,min_periods=2).mean())
long['price_chg']=g['sell_price'].pct_change().replace([np.inf,-np.inf],0)
for c in ['dept_id','cat_id','store_id','state_id']: long[c+'_e']=long[c].astype('category').cat.codes
FEAT=['lag7','lag28','rmean7','rmean28','rmean56','price','price_rel','price_chg','wday','month','snap','event','dept_id_e','cat_id_e','store_id_e','state_id_e']
long['price']=long['price'].fillna(long['price'].median()); long['price_rel']=long['price_rel'].fillna(1.0); long['price_chg']=long['price_chg'].fillna(0.0)
long=long.dropna(subset=['lag28','rmean28'])
dmax=long['dnum'].max(); test_lo=dmax-HTEST+1; tr=long[long['dnum']<test_lo]; te=long[long['dnum']>=test_lo]
def scale_of(s): d=np.abs(np.diff(s.values)); return d.mean() if len(d) and d.mean()>0 else 1.0
sc=tr.groupby('id')['sales'].apply(scale_of); te=te.merge(sc.rename('scale'),left_on='id',right_index=True,how='left')
Xtr=tr[FEAT].values.astype('float32'); ytr=tr['sales'].values.astype('float32'); Xte=te[FEAT].values.astype('float32'); yte=te['sales'].values.astype('float32')
scl=np.where(te['scale'].values>0,te['scale'].values,1.0)
lg("features ready tr=%d te=%d nser=%d %.0fs; training 9 quantiles"%(len(Xtr),len(Xte),NSER,time.time()-t0))
GB={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=120,max_depth=5,learning_rate=0.08,max_bins=128); m.fit(Xtr,ytr); GB[t]=np.clip(m.predict(Xte),0,None)
def spl(P): return sum(np.mean(pin(yte,P[t],t)/scl) for t in TAUS)/len(TAUS)
BASE={t:float(np.quantile(ytr,t)) for t in TAUS}
out={'note':'M5-Uncertainty improved (ai2): +sell_prices features, %d series, calendar+lags. Level-12 unweighted scaled pinball loss (SPL) over 9 quantiles, last-28-day OOS.'%NSER,'n_series':NSER,'n_test':int(len(yte)),
 'SPL_gbm_quantile':round(float(spl(GB)),4),'SPL_baseline_empirical':round(float(spl({t:np.full(len(yte),BASE[t]) for t in TAUS})),4),
 'prior_run_no_price_1200series':0.2595,'reference':'M5-Uncertainty Level-12: winners ~0.16-0.17, naive benchmark ~0.22-0.25'}
out['improvement_vs_baseline_pct']=round((1-out['SPL_gbm_quantile']/out['SPL_baseline_empirical'])*100,1)
json.dump(out,open(os.path.expanduser("~/sean_dev/GBC_data/m5_full_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
