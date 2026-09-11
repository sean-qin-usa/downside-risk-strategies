# AMORTIZED-AS-PRIOR (Gibbs / partial-pooling) vs naive results.
# Fix for the backwards-blend finding: treat the pooled amortized model as the PRIOR;
# let a name's own data apply only a shrinkage-weighted AFFINE (level/scale) correction,
# weight = age/(age+K), so young names stay at the prior and mature names get a light own-data refinement.
# Runs fully in-sandbox from the saved CRSP panel (no WRDS/Bloomberg).
import json, os, math, time
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
P="/sessions/gifted-sleepy-noether/mnt/GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
r=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv")); r['date']=pd.to_datetime(r['date'])
r['ret']=pd.to_numeric(r['ret'],errors='coerce')*100.0; r=r.dropna(subset=['ret']).sort_values(['permno','date']).reset_index(drop=True)
ch=pd.read_csv(os.path.join(P,"crsp_panel_chars.csv"))
lg("loaded returns %d rows, %d names %.0fs"%(len(r),r.permno.nunique(),time.time()-t0))
g=r.groupby('permno',sort=False)
r['age']=g.cumcount()
r['lag1']=g['ret'].shift(1); r['abs1']=r['lag1'].abs()
# rolling features (causal): compute rolling then shift within group
r['rv5']=g['ret'].transform(lambda x:x.rolling(5,min_periods=3).std().shift(1))
r['rv21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).std().shift(1))
r['mean21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).mean().shift(1))
r['dn']=(r['lag1']<0).astype(float)
# causal expanding own mean/std up to t-1 (vectorized)
r['ret2']=r['ret']**2
csum=g['ret'].cumsum()-r['ret']; csum2=g['ret2'].cumsum()-r['ret2']; cnt=r['age'].values.astype(float)
with np.errstate(invalid='ignore',divide='ignore'):
    own_mean=np.where(cnt>0,csum/np.maximum(cnt,1),0.0)
    own_var=np.where(cnt>1,csum2/np.maximum(cnt,1)-own_mean**2,np.nan)
r['own_mean']=own_mean; r['own_std']=np.sqrt(np.clip(own_var,1e-6,None))
# chars
ch['logmcap']=np.log(np.maximum(pd.to_numeric(ch['mcap_mm'],errors='coerce').fillna(300.0),1.0))
for c in ['sector','beta','annvol']: ch[c]=pd.to_numeric(ch[c],errors='coerce')
r=r.merge(ch[['permno','logmcap','sector','beta','annvol','cohort']],on='permno',how='left')
r['sector']=r['sector'].fillna(-1); r['beta']=r['beta'].fillna(1.0); r['annvol']=r['annvol'].fillna(0.3)
r['rv5']=r['rv5'].fillna(r['rv21']).fillna(2.0); r['rv21']=r['rv21'].fillna(2.0); r['mean21']=r['mean21'].fillna(0.0)
r=r.dropna(subset=['lag1']); r['abs1']=r['abs1'].fillna(r['abs1'].median())
XC=['lag1','abs1','rv5','rv21','mean21','dn','age','logmcap','sector','beta','annvol']
# split names 60/40
rng=np.random.default_rng(11); names=r['permno'].unique(); rng.shuffle(names)
hold=set(names[:int(len(names)*0.4)]); tr=r[~r.permno.isin(hold)]; te=r[r.permno.isin(hold)].reset_index(drop=True)
lg("train %d rows, holdout %d rows, fitting %d quantile models %.0fs"%(len(tr),len(te),len(TAUS),time.time()-t0))
AM={}
for tau in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=tau,max_iter=140,max_depth=3,learning_rate=0.07,max_bins=128)
    m.fit(tr[XC].values,tr['ret'].values); AM[tau]=m.predict(te[XC].values); lg("  tau %.2f done %.0fs"%(tau,time.time()-t0))
AMarr={tau:AM[tau] for tau in TAUS}
med=AMarr[0.50]; amort_std=np.maximum((AMarr[0.90]-AMarr[0.10])/2.563,1e-3)  # implied sigma from pooled model
y=te['ret'].values; age=te['age'].values.astype(float); own_mean=te['own_mean'].values; own_std=te['own_std'].values
K=80.0; w=age/(age+K)  # own-data weight; ->0 young, ->1 mature
b=1.0+w*(np.clip(own_std,1e-3,None)/amort_std-1.0)      # scale correction toward prior(1)
a=w*(own_mean-med)                                       # level correction toward prior(0)
tnorm={0.05:-1.645,0.10:-1.282,0.25:-0.674,0.50:0.0,0.75:0.674,0.90:1.282,0.95:1.645}
# accumulate pinball by method and age bucket
BUCK=[('d15_30',15,30),('d30_60',30,60),('d60_120',60,120),('d120_250',120,250),('d250_500',250,500),('d500_1000',500,1000),('d1000_2700',1000,2700)]
def pit(name,qfun):
    out={}
    for bn,lo,hi in BUCK:
        m=(age>=lo)&(age<hi)&(age>=12)
        if m.sum()<50: continue
        loss=np.mean([pin(y[m],qfun(tau)[m],tau) for tau in TAUS])
        out[bn]=(round(float(loss),4),int(m.sum()))
    return out
q_amort=lambda tau: AMarr[tau]
q_gibbs=lambda tau: med + a + b*(AMarr[tau]-med)                       # amortized prior + shrinkage affine
q_ownpar=lambda tau: own_mean + np.clip(own_std,1e-3,None)*tnorm[tau]  # own EWMA-ish parametric (no pooling)
res={'note':'Amortized-as-prior (Gibbs): q = amort_median + a + b*(amort_q - amort_median); a,b shrink to prior (0,1) with weight age/(age+K), K=80. Compares vs pure amortized and own-only parametric. Pinball avg over 7 taus, held-out CRSP names.','K':K,'n_train':int(len(tr)),'n_holdout_names':len(hold),'curve':{}}
A=pit('amort',q_amort); G=pit('gibbs',q_gibbs); O=pit('ownpar',q_ownpar)
for bn,lo,hi in BUCK:
    if bn in A and bn in G:
        am=A[bn][0]; gb=G[bn][0]; ow=O.get(bn,(None,))[0]
        res['curve'][bn]=dict(n=A[bn][1],amortized=am,gibbs_prior=gb,own_parametric=ow,gibbs_vs_amort=round(gb/am,4),gibbs_improves=bool(gb<am))
json.dump(res,open(os.path.join(P,"amort_gibbs.json"),"w"),indent=2,default=str)
# chart
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    ks=list(res['curve'].keys()); x=np.arange(len(ks))
    fig,ax=plt.subplots(1,2,figsize=(15,5.5))
    ax[0].plot(x,[res['curve'][k]['amortized'] for k in ks],'o-',color='#d62728',lw=2,label='pure amortized (prior only)')
    ax[0].plot(x,[res['curve'][k]['gibbs_prior'] for k in ks],'^-',color='#2ca02c',lw=2,label='amortized-as-prior + Gibbs affine')
    ax[0].plot(x,[res['curve'][k]['own_parametric'] for k in ks],'s-',color='#7f7f7f',lw=1.5,label='own-only parametric (no pooling)')
    ax[0].set_xticks(x); ax[0].set_xticklabels([k[1:] for k in ks],rotation=45); ax[0].set_xlabel('listing age (days)'); ax[0].set_ylabel('avg pinball (lower=better)')
    ax[0].set_title('Gibbs prior-update refines the amortized prior at maturity, holds at prior when young'); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].axhline(1.0,color='k',ls='--',lw=.7); ax[1].plot(x,[res['curve'][k]['gibbs_vs_amort'] for k in ks],'^-',color='#2ca02c',lw=2)
    ax[1].set_xticks(x); ax[1].set_xticklabels([k[1:] for k in ks],rotation=45); ax[1].set_xlabel('listing age (days)'); ax[1].set_ylabel('Gibbs / amortized (<1 = Gibbs better)')
    ax[1].set_title('Gibbs vs pure amortized (ratio)'); ax[1].grid(alpha=.3)
    plt.tight_layout(); plt.savefig(os.path.join(P,"amort_gibbs.png"),dpi=120); plt.close()
except Exception as e: lg("chart err %s"%str(e)[:100])
lg("AMORT_GIBBS\n"+json.dumps(res['curve'],indent=2,default=str)); lg("DONE %.0fs"%(time.time()-t0))
