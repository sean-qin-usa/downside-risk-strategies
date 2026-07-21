# GARCH-RESIDUAL HYBRID (ai2) — the "completely match / beat everywhere" candidate.
# Motivation (cross-country result): standalone GARCH-t beats raw-GBM on almost every single asset; nonparam only wins
# where the parametric residual assumption is badly broken (crisis FX, turbulence). The fix that should DOMINATE both:
# let GARCH model the VOL DYNAMICS (its strength) and let a nonparametric quantile model shape the STANDARDIZED
# RESIDUAL conditional on state (nonparam's strength). q_hybrid(tau)=mu + sigma_t * Qz(tau | state_t).
#   - If residuals are iid-t, Qz collapses to the constant t-quantile -> hybrid == GARCH (it NESTS GARCH, can't lose much).
#   - If residual SHAPE is state-dependent (fat-tail-in-fat-tail after shocks), Qz adapts -> hybrid BEATS GARCH.
# Compare amortized(pooled) over CRSP: GARCH-t vs raw-GBM vs HYBRID, overall + by vol quintile + 5% breach. Predict hybrid best everywhere.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False)
names=cnt[cnt>=1500].index.tolist()[:200]
lg("names=%d  %.0fs"%(len(names),time.time()-t0))

RAWX=['lag1','abs1','prv5','prv21','rv63']                 # raw-return features (three_way style)
ZX  =['logsig','zl1','absz5','zstd21','fracdn5','sigpct']  # residual-state features for the hybrid
tr_raw=[]; te_raw=[]; tr_z=[]; te_z=[]
recs=[]                                                    # per test row bookkeeping
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float)
    n=len(y);
    if n<1500: continue
    sp=int(n*0.6)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception:
        continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6)
    tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1)
    df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['logsig']=np.log(np.maximum(df['sig'],1e-6))
    df['zl1']=df['z'].shift(1); df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1); df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['idx']=np.arange(n)
    df=df.dropna();
    sigpct=df['sig'].rank(pct=True); df['sigpct']=sigpct
    trn=df[df['idx']<sp]; tst=df[df['idx']>=sp]
    if len(tst)<30: continue
    tr_raw.append(trn[RAWX+['y']]); te_raw.append(tst[RAWX+['y']])
    tr_z.append(trn[ZX+['z']]);      te_z.append(tst[ZX+['z']])
    for _,row in tst.iterrows():
        recs.append((row['y'],mu,row['sig'],nu,tsc,row['prv21']))
lg("panels built n_test_rows=%d  %.0fs"%(len(recs),time.time()-t0))
TR_RAW=pd.concat(tr_raw); TE_RAW=pd.concat(te_raw); TR_Z=pd.concat(tr_z); TE_Z=pd.concat(te_z)
R=np.array(recs); Y=R[:,0]; MU=R[:,1]; SIG=R[:,2]; NU=R[:,3]; TSC=R[:,4]; PRV21=R[:,5]
# raw-GBM quantiles
rawq={}; hybq={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TR_RAW[RAWX].values,TR_RAW['y'].values)
    rawq[t]=m.predict(TE_RAW[RAWX].values)
    mz=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TR_Z[ZX].values,TR_Z['z'].values)
    zq=mz.predict(TE_Z[ZX].values)
    hybq[t]=MU+SIG*zq                                     # reconstruct hybrid return-quantile
    lg("  tau %.3f fit %.0fs"%(t,time.time()-t0))
def garch_q(t): return MU+SIG*stats.t.ppf(t,NU)/TSC
# vol quintiles by prv21
qcut=pd.qcut(PRV21,5,labels=['Q1_calm','Q2','Q3','Q4','Q5_turbulent'])
def scores(qfun_dict_or_fn):
    getq=(lambda t: qfun_dict_or_fn[t]) if isinstance(qfun_dict_or_fn,dict) else qfun_dict_or_fn
    pl=np.zeros(len(Y))
    for t in TAUS: pl+=pin(Y,getq(t),t)
    pl/=len(TAUS)
    br=(Y<(qfun_dict_or_fn[0.05] if isinstance(qfun_dict_or_fn,dict) else qfun_dict_or_fn(0.05))).mean()
    out={'overall':round(float(pl.mean()),4),'breach_5pct':round(float(br),4)}
    for q in ['Q1_calm','Q2','Q3','Q4','Q5_turbulent']:
        out[q]=round(float(pl[qcut==q].mean()),4)
    return out
S_g={t:garch_q(t) for t in TAUS}
res={'garch_t':scores(S_g),'raw_gbm':scores(rawq),'hybrid':scores(hybq)}
# head-to-head: hybrid vs garch (and vs raw) improvement %
def impr(a,b): return round(100*(b-a)/b,2)   # % hybrid better than baseline b
res['hybrid_vs_garch_pct']={k:impr(res['hybrid'][k],res['garch_t'][k]) for k in res['garch_t'] if k!='breach_5pct'}
res['hybrid_vs_rawgbm_pct']={k:impr(res['hybrid'][k],res['raw_gbm'][k]) for k in res['raw_gbm'] if k!='breach_5pct'}
out={'note':'GARCH-residual HYBRID vs GARCH-t vs raw-GBM, amortized over CRSP (%d names, %d test rows). '
            'q_hybrid=mu+sigma_t*Qz(tau|state); Qz = pooled GBM on GARCH-standardized residuals. Nests GARCH; should DOMINATE. '
            'By vol quintile (prv21). hybrid_vs_garch_pct>0 => hybrid better.'%(len(names),len(Y)),
     'n_names':len(names),'n_test':int(len(Y)),'results':res}
json.dump(out,open(os.path.join(D,"garch_gbm_hybrid_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
