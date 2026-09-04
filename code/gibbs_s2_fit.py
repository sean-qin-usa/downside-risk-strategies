# Stage 2: load cached features, fit quantile models, compute Gibbs-prior vs amortized results.
import os, json, time, warnings; warnings.filterwarnings("ignore")
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
P="/sessions/gifted-sleepy-noether/mnt/GBC Project"; t0=time.time()
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
d=np.load(os.path.join(P,"_gibbs_cache.npz"))
Xtr,ytr,Xte,y,age,om,os_=d['Xtr'],d['ytr'],d['Xte'],d['yte'],d['age'],d['own_mean'],d['own_std']
print("loaded tr=%d te=%d %.1fs"%(len(Xtr),len(Xte),time.time()-t0),flush=True)
AM={}
for tau in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=tau,max_iter=35,max_depth=3,learning_rate=0.12,max_bins=48)
    m.fit(Xtr,ytr); AM[tau]=m.predict(Xte); print("  tau %.2f %.1fs"%(tau,time.time()-t0),flush=True)
med=AM[0.50]; astd=np.maximum((AM[0.90]-AM[0.10])/2.563,1e-3)
K=80.0; w=age/(age+K); b=1.0+w*(np.clip(os_,1e-3,None)/astd-1.0); a=w*(om-med)
tn={0.05:-1.645,0.10:-1.282,0.25:-0.674,0.50:0.0,0.75:0.674,0.90:1.282,0.95:1.645}
BUCK=[('d15_30',15,30),('d30_60',30,60),('d60_120',60,120),('d120_250',120,250),('d250_500',250,500),('d500_1000',500,1000),('d1000_2700',1000,2700)]
qA=lambda t:AM[t]; qG=lambda t:med+a+b*(AM[t]-med); qO=lambda t:om+np.clip(os_,1e-3,None)*tn[t]
def loss(qf,m): return float(np.mean([pin(y[m],qf(t)[m],t) for t in TAUS]))
res={'note':'Amortized-as-prior (Gibbs): q=amort_med+a+b*(amort_q-amort_med); a,b shrink to prior(0,1), weight w=age/(age+80). vs pure amortized and own-only parametric. In-sandbox CRSP, 160 names (70 held out).','K':K,'n_train':int(len(Xtr)),'curve':{}}
for bn,lo,hi in BUCK:
    m=(age>=lo)&(age<hi)&(age>=12)
    if m.sum()<40: continue
    am=loss(qA,m); gb=loss(qG,m); ow=loss(qO,m)
    res['curve'][bn]=dict(n=int(m.sum()),amortized=round(am,4),gibbs_prior=round(gb,4),own_parametric=round(ow,4),gibbs_vs_amort=round(gb/am,4),gibbs_improves=bool(gb<am))
json.dump(res,open(os.path.join(P,"amort_gibbs.json"),"w"),indent=2,default=str)
print("DONE %.1fs"%(time.time()-t0),flush=True)
for k,v in res['curve'].items(): print(k,'amort',v['amortized'],'GIBBS',v['gibbs_prior'],'ownpar',v['own_parametric'],'g/a',v['gibbs_vs_amort'],v['gibbs_improves'],flush=True)
