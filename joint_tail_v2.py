# CO-CRASH v2 (ai2) — v1 was an honest negative: on a DIVERSIFIED 25-name largecap basket, multivariate GARCH (DCC/CCC)
# beat the direct GBM portfolio-quantile. Hypothesis for the negative: diversification washes out the co-crash the
# nonparametric model is supposed to catch. v2 tests that directly: does the GBM edge appear as the basket gets
# CONCENTRATED (few names, high co-movement) — where correlation-spike tail risk is NOT diversified away?
# Sweep basket size K in {2,3,5,10,25}; for each, direct GBM portfolio-quantile vs CCC-GARCH vs DCC-lite.
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
ch=pd.read_csv(os.path.join(D,"crsp_panel_chars.csv"))
lc=ch[ch['cohort']=='largecap']['permno'].tolist() if 'cohort' in ch else ch['permno'].tolist()
Wall=rr[rr.permno.isin(lc)].pivot_table(index='date',columns='permno',values='ret')
Wall=Wall.dropna(axis=1,thresh=int(0.9*len(Wall))).dropna()
# order names by average pairwise correlation (most co-moving first) so concentrated baskets are genuinely co-crash-prone
C=np.corrcoef(Wall.values.T); avgc=(C.sum(1)-1)/(C.shape[1]-1)
order=np.argsort(-avgc); cols=Wall.columns[order]
Wall=Wall[cols]
def run_basket(K):
    W=Wall.iloc[:,:K]; A=W.values; dates=W.index; N=A.shape[1]; port=A.mean(1); n=len(port); sp=int(n*0.6)
    vol=np.zeros((n,N)); nus=[]
    for j in range(N):
        y=A[:,j]
        try:
            p=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False).params
            om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nus.append(float(p.get('nu',8)))
        except Exception:
            om,al,be,mu=0.1,0.05,0.9,0.0; nus.append(8)
        e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
        for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
        vol[:,j]=np.sqrt(s2)
    nu_p=float(np.mean(nus)); Z=A/np.maximum(vol,1e-6); R_ccc=np.corrcoef(Z[:sp].T); w=np.ones(N)/N
    ps=lambda Vt,Rt: math.sqrt(max(w@(np.outer(Vt,Vt)*Rt)@w,1e-10))
    Qt=R_ccc.copy(); lam=0.97; dcc=np.zeros(n)
    for i in range(n):
        if i>0:
            z=Z[i-1]; Qt=(1-lam)*np.outer(z,z)+lam*Qt; dd=np.sqrt(np.clip(np.diag(Qt),1e-8,None)); Rt=Qt/np.outer(dd,dd)
        else: Rt=R_ccc
        dcc[i]=ps(vol[i],Rt)
    ccc=np.array([ps(vol[i],R_ccc) for i in range(n)])
    pf=pd.DataFrame({'y':port},index=dates)
    pf['lag1']=pf['y'].shift(1); pf['abs1']=pf['y'].abs().shift(1)
    pf['prv5']=pf['y'].rolling(5,min_periods=3).std().shift(1); pf['prv21']=pf['y'].rolling(21,min_periods=8).std().shift(1)
    pf['disp21']=pd.Series(A.std(1),index=dates).rolling(21,min_periods=8).mean().shift(1)
    pf['avgabs5']=pd.Series(np.abs(A).mean(1),index=dates).rolling(5,min_periods=3).mean().shift(1)
    pf['fracdn1']=pd.Series((A<0).mean(1),index=dates).shift(1)
    pf['comov21']=pd.Series((np.abs(A).mean(1))/(A.std(1)+1e-6),index=dates).rolling(21,min_periods=8).mean().shift(1)
    PXC=['lag1','abs1','prv5','prv21','disp21','avgabs5','fracdn1','comov21']; pf=pf.dropna()
    yv=pf['y'].values; nn=len(pf); s2i=int(nn*0.6)
    gbm={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=200,max_depth=3,learning_rate=0.06).fit(pf[PXC].values[:s2i],yv[:s2i]) for t in TAUS}
    GQ={t:gbm[t].predict(pf[PXC].values[s2i:]) for t in TAUS}
    td=pf.index[s2i:]; di={d:i for i,d in enumerate(dates)}; tsc=math.sqrt(nu_p/(nu_p-2)) if nu_p>2 else 1.0
    def M(qf):
        pl=0.0; b=0; cnt=0
        for jj,dt_ in enumerate(td):
            i=di[dt_]; yi=port[i]; qs={t:qf(t,jj,i) for t in TAUS}
            pl+=np.mean([pin(yi,qs[t],t) for t in TAUS]); cnt+=1; b+=(yi<qs[0.025])
        return dict(pinball=round(pl/cnt,4),breach_2p5=round(b/cnt,4),n=cnt)
    qc=lambda t,jj,i: ccc[i]*stats.t.ppf(t,nu_p)/tsc
    qd=lambda t,jj,i: dcc[i]*stats.t.ppf(t,nu_p)/tsc
    qg=lambda t,jj,i: GQ[t][jj]
    # crisis decile by portfolio vol
    pv=ccc[[di[d] for d in td]]; thr=np.quantile(pv,0.9); mask=pv>=thr
    def Mm(qf):
        pl=0.0; b=0; cnt=0
        for jj,dt_ in enumerate(td):
            if not mask[jj]: continue
            i=di[dt_]; yi=port[i]; qs={t:qf(t,jj,i) for t in TAUS}
            pl+=np.mean([pin(yi,qs[t],t) for t in TAUS]); cnt+=1; b+=(yi<qs[0.025])
        return dict(pinball=round(pl/cnt,4),breach_2p5=round(b/cnt,4),n=cnt) if cnt else None
    return dict(K=K,avg_pairwise_corr=round(float(avgc[order][:K].mean()),3),n_test=len(td),nu_p=round(nu_p,1),
                all={'CCC':M(qc),'DCC':M(qd),'GBM':M(qg)},
                crisis={'CCC':Mm(qc),'DCC':Mm(qd),'GBM':Mm(qg)})
res=[]
for K in [2,3,5,10,25]:
    r=run_basket(K); res.append(r); lg("K=%d done  GBM %.4f / DCC %.4f / CCC %.4f  %.0fs"%(K,r['all']['GBM']['pinball'],r['all']['DCC']['pinball'],r['all']['CCC']['pinball'],time.time()-t0))
out={'note':'Co-crash v2: does the direct GBM portfolio-quantile edge over multivariate GARCH emerge as the basket gets CONCENTRATED '
            '(few high-comovement names) where co-crash is not diversified away? Names ordered by avg pairwise corr; basket = top-K. '
            'Per K: overall + crisis-decile pinball for CCC-GARCH / DCC-lite / GBM_direct. Win = GBM pinball < min(CCC,DCC), esp. in crisis.',
     'baskets':res}
json.dump(out,open(os.path.join(D,"joint_tail_v2_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
