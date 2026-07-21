import os,json,time,warnings; warnings.filterwarnings("ignore")
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
t0=time.time(); d=np.load("_gibbs_cache.npz")
Xtr,ytr,Xte,yte=d['Xtr'],d['ytr'],d['Xte'],d['yte']
TAUS=[0.05,0.5,0.95]
def pin(y,q,t): e=y-q; return np.where(e>=0,t*e,(t-1)*e)
FN=['lag1','abs1','rv5','rv21','mean21','dn','age','logmcap','sector','beta','annvol']
SUB={'ALL':list(range(11)),'chars_only[age+mcap+sector+beta+annvol]':[6,7,8,9,10],
 'own_recent_only[lag/absvol]':[0,1,2,3,4,5],'no_realized_vol[-rv5,rv21]':[0,1,4,5,6,7,8,9,10],
 'no_lags[-lag1,abs1,dn]':[2,3,4,6,7,8,9,10],'no_age':[0,1,2,3,4,5,7,8,9,10],
 'no_chars[-mcap,sector,beta,annvol]':[0,1,2,3,4,5,6]}
res={}
for nm,cols in SUB.items():
    tot=0.0
    for t in TAUS:
        m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=40,max_depth=3,learning_rate=0.12,max_bins=48)
        m.fit(Xtr[:,cols],ytr); tot+=np.mean(pin(yte,m.predict(Xte[:,cols]),t))
    res[nm]=round(float(tot/len(TAUS)),4)
base=res['ALL']
out={'note':'Feature ablation of amortized quantile model (reuse cached CRSP panel, 160 names). Avg pinball over taus 0.05/0.5/0.95, held-out names. pct_worse_than_ALL = how much OOS pinball rises when that feature group is removed (bigger = more important).','ALL_pinball':base,
 'subsets':{k:{'pinball':v,'pct_vs_ALL':round((v/base-1)*100,1)} for k,v in sorted(res.items(),key=lambda x:x[1])}}
json.dump(out,open("amort_ablation.json","w"),indent=2)
print(json.dumps(out,indent=2)); print("%.1fs"%(time.time()-t0))
