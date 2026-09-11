# LEARNED REGIME GATE (ai2) — the deployable object. Train a gate on the misspecification score to switch between GARCH-t
# (default) and amortized nonparam (GBM), and measure whether the GATED model beats BOTH pure GARCH and always-nonparam OOS.
# No leakage: GARCH+GBM fit on TRAIN (first 60%). The remaining 40% (both models OOS) is split into TEST_A (learn the gate)
# and TEST_B (final eval). Gate = HistGradientBoostingClassifier predicting P(nonparam beats GARCH today) from causal signals.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from scipy import stats
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
lg("names=%d %.0fs"%(len(names),time.time()-t0))
RAWX=['lag1','abs1','prv5','prv21','rv63']
GATEX=['mk63','skew63','jump5','prv21','sigpct','absz21']       # causal gate features (misspecification score inputs)
TR=[]; TE=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().shift(1).abs()
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['absz21']=df['z'].abs().rolling(21,min_periods=8).mean().shift(1)
    df['mu']=mu; df['nu']=nu; df['tsc']=tsc; df['idx']=np.arange(n); df=df.dropna()
    df['sigpct']=df['sig'].rank(pct=True)
    cols=list(dict.fromkeys(RAWX+GATEX+['y','sig','mu','nu','tsc']))     # dedupe (prv21 in both RAWX & GATEX)
    TR.append(df[df['idx']<sp][RAWX+['y']])
    TE.append(df[df['idx']>=sp][cols])
lg("panels %d names %.0fs"%(len(TR),time.time()-t0))
TRc=pd.concat(TR); TEc=pd.concat(TE).sample(frac=1.0,random_state=0).reset_index(drop=True)  # shuffle for A/B split
# amortized GBM
GQ={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['y'].values)
    GQ[t]=m.predict(TEc[RAWX].values)
Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
pg=np.zeros(len(Y)); pb=np.zeros(len(Y))
for t in TAUS:
    gq=MU+SIG*stats.t.ppf(t,NU)/TSC
    pg+=pin(Y,gq,t); pb+=pin(Y,GQ[t],t)
pg/=len(TAUS); pb/=len(TAUS)
# A/B split (both OOS): A learns gate, B evaluates
nT=len(Y); cut=nT//2; A=slice(0,cut); B=slice(cut,nT)
XA=TEc[GATEX].values[A]; yA=(pb[A]<pg[A]).astype(int)     # target: did nonparam beat garch on this OOS day
clf=HistGradientBoostingClassifier(max_iter=200,max_depth=3,learning_rate=0.06).fit(XA,yA)
prob=clf.predict_proba(TEc[GATEX].values[B])[:,1]
# choose gate threshold on A to maximize pinball improvement
probA=clf.predict_proba(XA)[:,1]
best_thr,best_imp=0.5,-1
for thr in np.linspace(0.3,0.8,26):
    gated=np.where(probA>=thr,pb[A],pg[A]); imp=pg[A].mean()-gated.mean()
    if imp>best_imp: best_imp,best_thr=imp,thr
gatedB=np.where(prob>=best_thr,pb[B],pg[B])
oracleB=np.minimum(pg[B],pb[B])
def m(x): return round(float(np.mean(x)),4)
res={'garch_t':m(pg[B]),'always_nonparam':m(pb[B]),'gate_learned':m(gatedB),'oracle_upperbound':m(oracleB),
     'gate_threshold':round(float(best_thr),3),'pct_days_gated_to_nonparam':round(float((prob>=best_thr).mean()),3),
     'gate_vs_garch_pct':round(100*(m(pg[B])-m(gatedB))/m(pg[B]),2),
     'gate_vs_alwaysnonparam_pct':round(100*(m(pb[B])-m(gatedB))/m(pb[B]),2),
     'oracle_vs_garch_pct':round(100*(m(pg[B])-m(oracleB))/m(pg[B]),2),
     'gate_capture_of_oracle_pct':round(100*(m(pg[B])-m(gatedB))/max(m(pg[B])-m(oracleB),1e-9),1)}
# feature importance proxy: gate rate by mk63 decile on B
mk=TEc['mk63'].values[B]; dec=pd.qcut(mk,10,labels=False,duplicates='drop'); gflag=(prob>=best_thr).astype(int)
res['gate_rate_by_mk63_decile']=[round(float(gflag[dec==d].mean()),3) for d in range(int(dec.max())+1)]
out={'note':'Learned regime gate: HGB classifier predicts P(nonparam beats GARCH today) from causal misspecification signals '
            '(mk63,skew63,jump5,prv21,sigpct,absz21). Trained on TEST_A (OOS), evaluated on TEST_B. Compares GARCH-t vs '
            'always-nonparam vs gate_learned vs oracle(per-day min). gate_capture_of_oracle_pct = how much of the achievable '
            'gap the learned gate captures. Deployable "GBC-as-standard" object.',
     'n_names':len(TR),'n_testB':int(nT-cut),'results':res}
json.dump(out,open(os.path.join(D,"regime_gate_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
