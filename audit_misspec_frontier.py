# MISSPECIFICATION FRONTIER (ai2) — operationalizes "high misspecification" and finds WHERE nonparam beats GARCH.
# "Misspecification" here = the GARCH-t model's own residual assumption failing IN A STATE-DEPENDENT way. GARCH-t assumes
# standardized residuals z=(r-mu)/sigma are iid Student-t with FIXED shape. It breaks when the residual SHAPE itself moves
# with state: fatter-than-t tails clustering after shocks, asymmetry after down-moves, jump clusters. Static fat tails alone
# don't hurt (nu absorbs them); it's the DRIFT/STATE-DEPENDENCE of the shape that GARCH can't track and nonparam can.
# We build 3 causal per-(name,day) misspecification signals and show the amortized-GBM-minus-GARCH pinball edge as a function
# of each. Prediction: edge ~0 at low misspecification (GARCH fine), rising monotonically to a large edge at high misspecification.
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
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
lg("names=%d %.0fs"%(len(names),time.time()-t0))
RAWX=['lag1','abs1','prv5','prv21','rv63']
TR=[]; TE=[]; META=[]
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
    # ---- misspecification signals (all causal, lag1) ----
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)            # recent residual excess kurtosis = fat-tail drift
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)        # recent jump magnitude (|z|)
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().shift(1).abs()    # recent residual asymmetry
    df['idx']=np.arange(n); df=df.dropna()
    trn=df[df['idx']<sp]; tst=df[df['idx']>=sp]
    if len(tst)<30: continue
    TR.append(trn[RAWX+['y']])
    te=tst[RAWX+['y','sig','mk63','jump5','skew63']].copy(); te['mu']=mu; te['nu']=nu; te['tsc']=tsc
    TE.append(te)
    META.append(pn)
lg("panels %d names %.0fs"%(len(META),time.time()-t0))
TRc=pd.concat(TR); TEc=pd.concat(TE).reset_index(drop=True)
# amortized GBM quantiles
GQ={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['y'].values)
    GQ[t]=m.predict(TEc[RAWX].values)
Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
pl_g=np.zeros(len(Y)); pl_b=np.zeros(len(Y))
for t in TAUS:
    gq=MU+SIG*stats.t.ppf(t,NU)/TSC
    pl_g+=pin(Y,gq,t); pl_b+=pin(Y,GQ[t],t)
pl_g/=len(TAUS); pl_b/=len(TAUS)
edge=pl_g-pl_b                                    # >0 => GBM (nonparam) better than GARCH
def frontier(sig_name):
    s=TEc[sig_name].values; ok=np.isfinite(s)
    dec=pd.qcut(s[ok],10,labels=False,duplicates='drop')
    out=[]
    for d in sorted(np.unique(dec)):
        mask=(dec==d)
        out.append(dict(decile=int(d)+1,
                        signal_mean=round(float(np.mean(s[ok][mask])),3),
                        garch_pin=round(float(pl_g[ok][mask].mean()),4),
                        gbm_pin=round(float(pl_b[ok][mask].mean()),4),
                        edge_abs=round(float(edge[ok][mask].mean()),5),
                        edge_pct=round(100*float(edge[ok][mask].mean())/float(pl_g[ok][mask].mean()),2),
                        n=int(mask.sum())))
    corr=float(np.corrcoef(s[ok],edge[ok])[0,1])
    return {'deciles':out,'corr_signal_edge':round(corr,3)}
out={'note':'Misspecification frontier: amortized-GBM minus GARCH-t pinball EDGE as a function of causal per-(name,day) '
            'misspecification signals. mk63=recent 63d standardized-residual excess kurtosis (fat-tail drift); '
            'jump5=recent 5d max|z| (jump magnitude); skew63=|recent 63d residual skew| (asymmetry drift). '
            'edge_pct>0 => nonparam better. Prediction: edge rises monotonically with misspecification; ~0 in bottom deciles.',
     'n_names':len(META),'n_test':int(len(Y)),
     'overall_edge_pct':round(100*float(edge.mean())/float(pl_g.mean()),2),
     'by_mk63_residkurt':frontier('mk63'),'by_jump5':frontier('jump5'),'by_skew63':frontier('skew63')}
json.dump(out,open(os.path.join(D,"misspec_frontier_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
