# "MORE TURKEYS" — test first-principles predictions of where nonparametric beats GARCH, with SEASONAL/CALENDAR features added.
# Principle: nonparam wins where conditional SHAPE changes with state AND the change is LEARNABLE (regime/seasonality/trend), not random fat tails.
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
def extract_dated(pdf):
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vcol=pdf.columns[cols.index('value')]; dcol=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dcol,vcol]].dropna().copy(); s[dcol]=pd.to_datetime(s[dcol],errors='coerce'); s=s.dropna(subset=[dcol])
        return s.set_index(dcol)[vcol].sort_index().astype(float)
    num=pdf.select_dtypes('number')
    return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
SER={'FX_TRY':'USDTRY Curncy','FX_EGP':'USDEGP Curncy','FX_NGN':'USDNGN Curncy','FX_PKR':'USDPKR Curncy',
 'AG_corn':'C 1 Comdty','AG_wheat':'W 1 Comdty','AG_soy':'S 1 Comdty','AG_coffee':'KC1 Comdty','AG_sugar':'SB1 Comdty',
 'POWER_pjm':'PW1 Comdty','CREDIT_hyoas':'LF98OAS Index','CREDIT_igoas':'LUACOAS Index',
 'SOV_emb':'EMB US Equity','VOL_vix':'VIX Index','CTRL_spy':'SPY US Equity'}
TAUS=[0.01,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.99]
end=dt.date.today(); start=end-dt.timedelta(days=365*12)
def feats(r):  # r: dated pct returns
    df=pd.DataFrame({'r':r})
    df['lag1']=r.shift(1); df['lag2']=r.shift(2); df['abs1']=r.abs().shift(1)
    df['rv5']=r.rolling(5).std().shift(1); df['rv21']=r.rolling(21).std().shift(1); df['mean21']=r.rolling(21).mean().shift(1)
    df['dn']=(r.shift(1)<0).astype(float)
    mo=r.index.month; df['mo_sin']=np.sin(2*np.pi*mo/12); df['mo_cos']=np.cos(2*np.pi*mo/12)  # SEASONALITY
    return df.dropna()
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
Xc=['lag1','lag2','abs1','rv5','rv21','mean21','dn','mo_sin','mo_cos']
out={}
for nm,tk in SER.items():
    try:
        s=extract_dated(to_pd(blp.bdh(tk,'px_last',start,end)))
        if s is None or len(s)<800: out[nm]={'ticker':tk,'ok':False,'note':'no/short'}; lg(f"{nm} no data"); continue
        r=(np.log(s/s.shift(1)).replace([np.inf,-np.inf],np.nan).dropna())*100
        df=feats(r); n=len(df); cut=int(n*0.6); tr=df.iloc[:cut]; te=df.iloc[cut:]
        ytr=tr['r'].values; yte=te['r'].values; rtr=tr['r'].values
        am=arch_model(rtr-rtr.mean(),mean='Zero',vol='GARCH',p=1,o=1,q=1,dist='t').fit(disp='off')
        pr=am.params; om,al,ga,be,nu=float(pr['omega']),float(pr.get('alpha[1]',0)),float(pr.get('gamma[1]',0)),float(pr.get('beta[1]',0)),float(pr.get('nu',8))
        mu=float(rtr.mean()); rr=df['r'].values; h=np.empty(len(rr)); h[0]=np.var(rtr)
        for i in range(1,len(rr)):
            e=rr[i-1]-mu; h[i]=om+(al+ga*(e<0))*e*e+be*h[i-1]
            if not np.isfinite(h[i]) or h[i]<=0: h[i]=np.var(rtr)
        sig=np.sqrt(h)[cut:]; std=math.sqrt(nu/(nu-2)) if nu>2.05 else 1.0
        gp={tau:mu+sig*(sps.t.ppf(tau,nu)/std) for tau in TAUS}
        bp={}
        for tau in TAUS:
            m=GradientBoostingRegressor(loss='quantile',alpha=tau,n_estimators=100,max_depth=3,learning_rate=0.07,subsample=0.8,random_state=0)
            m.fit(tr[Xc].values,ytr); bp[tau]=m.predict(te[Xc].values)
        Lg=np.mean([pin(yte,gp[t],t) for t in TAUS],axis=0).mean(); Lb=np.mean([pin(yte,bp[t],t) for t in TAUS],axis=0).mean()
        out[nm]={'ticker':tk,'ok':True,'GARCH':round(float(Lg),4),'GBM':round(float(Lb),4),'ratio':round(float(Lb/Lg),3),'winner':'GBM(nonparam)' if Lb<Lg else 'GARCH','n_test':int(len(te))}
        lg(f"{nm}: GARCH {out[nm]['GARCH']} GBM {out[nm]['GBM']} ratio {out[nm]['ratio']} -> {out[nm]['winner']}")
    except Exception as e:
        out[nm]={'ticker':tk,'ok':False,'err':str(e)[:100]}; lg(f"{nm} ERR {str(e)[:80]}")
out['_note']='ratio<1 => nonparam beats GARCH. Features include month-seasonality. Tests first-principles: nonparam wins where SHAPE changes with LEARNABLE state (regime/seasonality), not just fat tails.'
json.dump(out,open(os.path.join(P,"frontier2.json"),"w"),indent=2,default=str)
lg("FRONTIER2_DONE %.0fs"%(time.time()-t0))
