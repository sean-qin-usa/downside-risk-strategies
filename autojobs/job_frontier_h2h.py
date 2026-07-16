# FRONTIER HEAD-TO-HEAD: GARCH-t (parametric) vs gradient-boosted quantile regression (distribution-free, IQN stand-in)
# across domains. Tests: nonparametric wins where GARCH is MISSPECIFIED (EM-FX, copper), ties/loses on well-specified (SPY).
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
def extract(pdf):
    if pdf is None or not len(pdf): return np.array([])
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols:
        vcol=pdf.columns[cols.index('value')]; dcol=[pdf.columns[i] for i,c in enumerate(cols) if 'date' in c]
        if dcol: pdf=pdf.sort_values(dcol[0])
        return pd.to_numeric(pdf[vcol],errors='coerce').dropna().values.astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().values.astype(float) if num.shape[1] else np.array([])
SER={'USDARS':'USDARS Curncy','USDTRY':'USDTRY Curncy','USDRUB':'USDRUB Curncy','COPPER':'HG1 Comdty','CORN':'C 1 Comdty',
     'SPY_ctrl':'SPY US Equity','TLT_ctrl':'TLT US Equity'}
TAUS=[0.01,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.99]
end=dt.date.today(); start=end-dt.timedelta(days=365*11)
def feats(r):  # r: pd.Series pct returns; build lagged state, target = r_t
    df=pd.DataFrame({'r':r})
    df['lag1']=r.shift(1); df['lag2']=r.shift(2); df['lag3']=r.shift(3)
    df['abs1']=r.abs().shift(1); df['rv5']=r.rolling(5).std().shift(1); df['rv21']=r.rolling(21).std().shift(1)
    df['mean5']=r.rolling(5).mean().shift(1); df['dn']=(r.shift(1)<0).astype(float)
    df=df.dropna()
    return df
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
out={}
for nm,tk in SER.items():
    try:
        vals=extract(to_pd(blp.bdh(tk,'px_last',start,end)))
        s=pd.Series(vals).astype(float); r=(np.log(s/s.shift(1)).replace([np.inf,-np.inf],np.nan).dropna())*100
        if len(r)<800: out[nm]={'err':'short'}; continue
        r.index=range(len(r)); df=feats(r); Xcols=['lag1','lag2','lag3','abs1','rv5','rv21','mean5','dn']
        n=len(df); cut=int(n*0.6); tr=df.iloc[:cut]; te=df.iloc[cut:]
        ytr=tr['r'].values; yte=te['r'].values; Xtr=tr[Xcols].values; Xte=te[Xcols].values
        # --- GARCH-t: fit on train returns, filter conditional vol across full, eval test ---
        rtr=tr['r'].values
        am=arch_model(rtr-rtr.mean(),mean='Zero',vol='GARCH',p=1,o=1,q=1,dist='t').fit(disp='off')
        pr=am.params; om,al,ga,be,nu=float(pr['omega']),float(pr.get('alpha[1]',0)),float(pr.get('gamma[1]',0)),float(pr.get('beta[1]',0)),float(pr.get('nu',8))
        mu=float(rtr.mean()); rr=df['r'].values; h=np.empty(len(rr)); h[0]=np.var(rtr)
        for i in range(1,len(rr)):
            e=rr[i-1]-mu; h[i]=om+(al+ga*(e<0))*e*e+be*h[i-1]
            if not np.isfinite(h[i]) or h[i]<=0: h[i]=np.var(rtr)
        sig=np.sqrt(h)[cut:]  # test-period conditional vol
        std=math.sqrt(nu/(nu-2)) if nu>2.05 else 1.0
        gp={tau: mu+sig*(sps.t.ppf(tau,nu)/std) for tau in TAUS}
        # --- GBM quantile regression (nonparametric) ---
        bp={}
        for tau in TAUS:
            m=GradientBoostingRegressor(loss='quantile',alpha=tau,n_estimators=150,max_depth=3,learning_rate=0.06,subsample=0.8,random_state=0)
            m.fit(Xtr,ytr); bp[tau]=m.predict(Xte)
        # pinball
        Lg=np.mean([pin(yte,gp[tau],tau) for tau in TAUS],axis=0).mean()
        Lb=np.mean([pin(yte,bp[tau],tau) for tau in TAUS],axis=0).mean()
        # tail-only (tau<=.10 and >=.90)
        tails=[0.01,0.05,0.10,0.90,0.95,0.99]
        Lgt=np.mean([pin(yte,gp[tau],tau) for tau in tails],axis=0).mean()
        Lbt=np.mean([pin(yte,bp[tau],tau) for tau in tails],axis=0).mean()
        out[nm]={'ticker':tk,'n_test':int(len(te)),'GARCH_pinball':round(float(Lg),4),'GBM_pinball':round(float(Lb),4),
                 'ratio_GBM_over_GARCH':round(float(Lb/Lg),3),'winner':'GBM(nonparam)' if Lb<Lg else 'GARCH',
                 'tail_GARCH':round(float(Lgt),4),'tail_GBM':round(float(Lbt),4),'tail_ratio':round(float(Lbt/Lgt),3)}
        lg(f"{nm}: GARCH {out[nm]['GARCH_pinball']} vs GBM {out[nm]['GBM_pinball']} ratio {out[nm]['ratio_GBM_over_GARCH']} -> {out[nm]['winner']} | tail_ratio {out[nm]['tail_ratio']}")
    except Exception as e:
        import traceback; out[nm]={'ticker':tk,'err':traceback.format_exc()[-200:]}; lg(f"{nm} ERR {str(e)[:100]}")
out['_note']='ratio<1 => nonparametric (GBM quantile, IQN stand-in) BEATS GARCH-t. Expect <1 on misspecified (EM-FX/copper), ~1 or >1 on well-specified (SPY/TLT).'
json.dump(out,open(os.path.join(P,"frontier_h2h.json"),"w"),indent=2,default=str)
lg("FRONTIER_H2H_DONE %.0fs"%(time.time()-t0))
