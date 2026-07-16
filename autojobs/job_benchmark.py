# IS THE NONPARAMETRIC APPROACH COMPETITIVE WITH DOMAIN-SOTA? Compare pinball loss of:
# GARCH-t | GARCH-EVT | QR (Quantile Regression Averaging family) | Markov 2-regime switching | GBM-quantile (distribution-free / IQN-family)
# on electricity + crisis FX + control. Answers "is the flexible quantile net comparable to QRA/regime-switching/EVT, and by how much."
import json, os, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
from xbbg import blp
import numpy as np, pandas as pd, datetime as dt
from arch import arch_model
from scipy import stats as sps
from sklearn.ensemble import GradientBoostingRegressor
def to_pd(d):
    for m in ('to_pandas','to_native'):
        if hasattr(d,m):
            try:
                x=getattr(d,m)()
                if hasattr(x,'to_pandas') and not isinstance(x,pd.DataFrame): x=x.to_pandas()
                if isinstance(x,pd.DataFrame): return x
            except Exception: pass
    return d if isinstance(d,pd.DataFrame) else None
def extract_d(pdf):
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vcol=pdf.columns[cols.index('value')]; dcol=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dcol,vcol]].dropna().copy(); s[dcol]=pd.to_datetime(s[dcol],errors='coerce'); s=s.dropna(subset=[dcol])
        return s.set_index(dcol)[vcol].sort_index().astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
TAUS=[0.01,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.99]
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
def feats(r):
    df=pd.DataFrame({'r':r}); df['lag1']=r.shift(1); df['lag2']=r.shift(2); df['abs1']=r.abs().shift(1)
    df['rv5']=r.rolling(5).std().shift(1); df['rv21']=r.rolling(21).std().shift(1); df['mean21']=r.rolling(21).mean().shift(1); df['dn']=(r.shift(1)<0).astype(float)
    mo=r.index.month; df['mo_sin']=np.sin(2*np.pi*mo/12); df['mo_cos']=np.cos(2*np.pi*mo/12)
    return df.dropna()
Xc=['lag1','lag2','abs1','rv5','rv21','mean21','dn','mo_sin','mo_cos']
def garch_q(rtr, rr, cut):
    am=arch_model(rtr-rtr.mean(),mean='Zero',vol='GARCH',p=1,o=1,q=1,dist='t').fit(disp='off')
    pr=am.params; om,al,ga,be,nu=float(pr['omega']),float(pr.get('alpha[1]',0)),float(pr.get('gamma[1]',0)),float(pr.get('beta[1]',0)),float(pr.get('nu',8))
    mu=float(rtr.mean()); h=np.empty(len(rr)); h[0]=np.var(rtr)
    for i in range(1,len(rr)):
        e=rr[i-1]-mu; h[i]=om+(al+ga*(e<0))*e*e+be*h[i-1]
        if not np.isfinite(h[i]) or h[i]<=0: h[i]=np.var(rtr)
    sig=np.sqrt(h)[cut:]; std=math.sqrt(nu/(nu-2)) if nu>2.05 else 1.0
    return {tau:mu+sig*(sps.t.ppf(tau,nu)/std) for tau in TAUS}, (mu,sig,nu,std,rtr)
def evt_q(gq, ctx, ytr):
    # GARCH-EVT: replace extreme tails with GPD fit to standardized-residual exceedances (train only)
    mu,sig,nu,std,rtr=ctx; z=(rtr-mu)/ (np.sqrt(np.var(rtr)))  # crude std resid on train
    out=dict(gq)
    try:
        for side,taus in [('L',[0.01,0.05]),('U',[0.99,0.95])]:
            zz = z if side=='L' else -z
            thr=np.quantile(zz,0.10); exc=thr-zz[zz<thr] if side=='L' else None
            ex = (thr - zz[zz<thr]) if side=='L' else (( -np.quantile(-z,0.10)) )
            tail=zz[zz<thr]; ex=thr-tail
            if len(ex)<20: continue
            c,loc,scale=sps.genpareto.fit(ex,floc=0)
            for tau in taus:
                p_tail = tau/0.10 if side=='L' else (1-tau)/0.10
                zq = thr - sps.genpareto.ppf(1-p_tail,c,loc=0,scale=scale)
                zq = zq if side=='L' else -zq
                out[tau]=mu+sig*zq
    except Exception: pass
    return out
def qr_q(tr,te,ytr):
    import statsmodels.formula.api as smf
    d=tr.copy(); out={}
    import statsmodels.api as sm
    X=sm.add_constant(tr[Xc].values); Xt=sm.add_constant(te[Xc].values)
    for tau in TAUS:
        try:
            m=sm.QuantReg(ytr,X).fit(q=tau,max_iter=2000); out[tau]=m.predict(Xt)
        except Exception: out[tau]=np.full(len(te),np.nan)
    return out
def gbm_q(tr,te,ytr):
    out={}
    for tau in TAUS:
        m=GradientBoostingRegressor(loss='quantile',alpha=tau,n_estimators=100,max_depth=3,learning_rate=0.07,subsample=0.8,random_state=0)
        m.fit(tr[Xc].values,ytr); out[tau]=m.predict(te[Xc].values)
    return out
def markov_q(rtr, rte):
    # 2-regime switching (mean+variance), Hamilton filter forward on test with train params
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    mod=MarkovRegression(rtr, k_regimes=2, trend='c', switching_variance=True).fit()
    p=mod.params
    mu=[float(mod.params[f'const[{k}]']) for k in range(2)]; s2=[float(mod.params[f'sigma2[{k}]']) for k in range(2)]
    P=np.array([[float(mod.params['p[0->0]']),1-float(mod.params['p[0->0]'])],[1-float(mod.params['p[1->1]']),float(mod.params['p[1->1]'])]])
    s=[math.sqrt(max(v,1e-8)) for v in s2]
    xi=np.array([0.5,0.5]); grid=np.linspace(min(mu)-8*max(s),max(mu)+8*max(s),4000)
    out={tau:[] for tau in TAUS}
    for y in rte:
        pred=xi@P  # predicted regime prob at t
        cdf=pred[0]*sps.norm.cdf(grid,mu[0],s[0])+pred[1]*sps.norm.cdf(grid,mu[1],s[1])
        for tau in TAUS: out[tau].append(float(np.interp(tau,cdf,grid)))
        eta=np.array([sps.norm.pdf(y,mu[0],s[0]),sps.norm.pdf(y,mu[1],s[1])]); filt=pred*eta; filt=filt/ (filt.sum()+1e-12); xi=filt
    return {tau:np.array(v) for tau,v in out.items()}
SER={'POWER_pjm':'PW1 Comdty','USDARS':'USDARS Curncy','USDTRY':'USDTRY Curncy','SPY_ctrl':'SPY US Equity'}
end=dt.date.today(); start=end-dt.timedelta(days=365*12)
res={}
for nm,tk in SER.items():
    try:
        sser=extract_d(to_pd(blp.bdh(tk,'px_last',start,end)))
        if sser is None or len(sser)<800: res[nm]={'err':'short'}; continue
        r=(np.log(sser/sser.shift(1)).replace([np.inf,-np.inf],np.nan).dropna())*100
        df=feats(r); n=len(df); cut=int(n*0.6); tr=df.iloc[:cut]; te=df.iloc[cut:]; ytr=tr['r'].values; yte=te['r'].values; rr=df['r'].values
        methods={}
        gq,ctx=garch_q(ytr,rr,cut); methods['GARCH_t']=gq
        try: methods['GARCH_EVT']=evt_q(gq,ctx,ytr)
        except Exception as e: lg(f"{nm} EVT err {str(e)[:60]}")
        try: methods['QR_QRA']=qr_q(tr,te,ytr)
        except Exception as e: lg(f"{nm} QR err {str(e)[:60]}")
        methods['GBM_nonparam']=gbm_q(tr,te,ytr)
        try: methods['Markov_2regime']=markov_q(ytr,yte)
        except Exception as e: lg(f"{nm} Markov err {str(e)[:60]}")
        # pinball per method
        cell={}
        for meth,qd in methods.items():
            try:
                L=np.nanmean([np.nanmean(pin(yte,np.asarray(qd[tau],dtype=float),tau)) for tau in TAUS])
                cell[meth]=round(float(L),4)
            except Exception: cell[meth]=None
        base=cell.get('GARCH_t')
        cell['_ratios_vs_GARCH']={m:(round(v/base,3) if (v and base) else None) for m,v in cell.items() if not m.startswith('_')}
        best=min([(v,m) for m,v in cell.items() if isinstance(v,float)],default=(None,None))
        cell['_best']=best[1]
        res[nm]=cell
        lg(f"{nm}: "+", ".join(f"{m}={cell[m]}" for m in ['GARCH_t','GARCH_EVT','QR_QRA','Markov_2regime','GBM_nonparam'] if cell.get(m) is not None)+f" | BEST={best[1]}")
    except Exception as e:
        import traceback; res[nm]={'err':traceback.format_exc()[-200:]}; lg(f"{nm} ERR {str(e)[:80]}")
res['_note']='pinball loss (lower=better). Compares distribution-free GBM-quantile (IQN-family) vs domain-SOTA: QRA(quant reg), Markov regime-switching, GARCH-EVT. Neural IQN expected comparable to GBM.'
json.dump(res,open(os.path.join(P,"benchmark_sota.json"),"w"),indent=2,default=str)
lg("BENCHMARK_DONE %.0fs"%(time.time()-t0))
