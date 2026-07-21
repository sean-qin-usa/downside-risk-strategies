# CRYPTO HOURLY (host, Bloomberg bdib) — P3 of the plan. High-frequency is where IQN previously showed a ~0.6% edge; extend
# with significance. Pull hourly bars for BTC/ETH/others via blp.bdib (intraday history is limited, ~months), build hourly
# returns, GBM vs GARCH-t with per-date(hour) Diebold-Mariano + resid_kurt. Defensive: skip failed days/tickers.
import json, os, time, math, warnings; warnings.filterwarnings("ignore")
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
from xbbg import blp
import numpy as np, pandas as pd, datetime as dt
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
def to_pd(d):
    for m in ('to_pandas','to_native'):
        if hasattr(d,m):
            try:
                x=getattr(d,m)()
                if hasattr(x,'to_pandas') and not isinstance(x,pd.DataFrame): x=x.to_pandas()
                if isinstance(x,pd.DataFrame): return x
            except Exception: pass
    return d if isinstance(d,pd.DataFrame) else None
def hourly(tk,ndays=180):
    end=dt.date.today(); frames=[]
    for k in range(ndays):
        day=end-dt.timedelta(days=k)
        try:
            b=to_pd(blp.bdib(ticker=tk,dt=day.strftime('%Y-%m-%d'),session='allday',interval=60))
            if b is None or not len(b): continue
            cols={str(c).lower():c for c in b.columns}
            cc=cols.get('close') or cols.get('value') or list(b.columns)[-1]
            s=b[cc].dropna()
            if len(s): frames.append(pd.Series(s.values,index=pd.to_datetime(b.index[:len(s)]) if not isinstance(b.index,pd.DatetimeIndex) else b.index[:len(s)]))
        except Exception: continue
    if not frames: return None
    s=pd.concat(frames).sort_index(); s=s[~s.index.duplicated()]
    return s.astype(float)
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
def feats(r):
    d=pd.DataFrame(index=r.index); d['y']=r.values
    d['lag1']=r.shift(1); d['abs1']=r.abs().shift(1); d['rv6']=r.rolling(6,min_periods=3).std().shift(1)
    d['rv24']=r.rolling(24,min_periods=8).std().shift(1); d['mean24']=r.rolling(24,min_periods=8).mean().shift(1); d['dn']=(r.shift(1)<0).astype(float)
    return d.dropna()
XC=['lag1','abs1','rv6','rv24','mean24','dn']
def nw_dm(d,lag=24):
    d=np.asarray(d,float); d=d[np.isfinite(d)]; T=len(d)
    if T<50: return None
    dd=d-d.mean(); v=np.mean(dd*dd)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(dd[k:]*dd[:-k])
    if v<=0: return None
    s=d.mean()/math.sqrt(v/T); return dict(DM=round(float(s),2),p=round(float(1-stats.norm.cdf(s)),4))
def h2h(r):
    from arch import arch_model
    D=feats(r); y=D['y'].values; n=len(D); sp=int(n*0.6)
    if n<800: return None
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: return None
    tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    e=y[:sp]-mu; s2=np.empty(sp); s2[0]=e.var()
    for k in range(1,sp): s2[k]=om+al*e[k-1]**2+be*s2[k-1]
    sig=np.empty(n); cur=s2[-1]
    for i in range(sp,n): cur=om+al*(y[i-1]-mu)**2+be*cur; sig[i]=math.sqrt(max(cur,1e-9))
    gq={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=150,max_depth=3,learning_rate=0.08).fit(D[XC].values[:sp],y[:sp]).predict(D[XC].values[sp:]) for t in TAUS}
    yte=y[sp:]; gper=np.zeros(len(yte)); nper=np.zeros(len(yte))
    for t in TAUS: gper+=pin(yte,mu+sig[sp:]*stats.t.ppf(t,nu)/tsc,t); nper+=pin(yte,gq[t],t)
    gper/=len(TAUS); nper/=len(TAUS)
    z=(y[:sp]-mu)/np.maximum(np.sqrt(s2),1e-6); rk=float(stats.kurtosis(z[np.isfinite(z)],fisher=False))
    return dict(garch=round(float(gper.mean()),4),nonparam=round(float(nper.mean()),4),ratio=round(float(nper.mean()/gper.mean()),4),n_oos=len(yte),resid_kurt=round(rk,1),DM=nw_dm(gper-nper))
TK=[('BTC','XBTUSD Curncy'),('ETH','XETUSD Curncy'),('XRP','XRPUSD Curncy'),('SOL','XSOUSD Curncy'),('DOGE','XDGUSD Curncy'),('LTC','XLCUSD Curncy')]
out={'note':'Crypto HOURLY: GBM vs GARCH-t on hourly returns with per-hour Diebold-Mariano + resid_kurt. Bloomberg bdib intraday '
            '(limited history). High-frequency crypto is where IQN previously edged GARCH ~0.6%; test with significance.','per_coin':{}}
for nm,tk in TK:
    try:
        s=hourly(tk)
        if s is None or len(s)<1000: lg("%s insufficient hourly (%s bars)"%(nm,0 if s is None else len(s))); continue
        r=(np.log(s/s.shift(1)).replace([np.inf,-np.inf],np.nan).dropna())*100.0
        hh=h2h(r)
        if hh is None: lg("%s h2h None (n=%d)"%(nm,len(r))); continue
        out['per_coin'][nm]=dict(ticker=tk,n_hours=len(r),**hh)
        lg("%-5s hourly n=%d ratio %s DM %s rkurt %s  %.0fs"%(nm,len(r),hh['ratio'],hh['DM'],hh['resid_kurt'],time.time()-t0))
        json.dump(out,open(os.path.join(P,"crypto_hourly.json"),"w"),indent=2,default=str)
    except Exception as ex: lg("%s ERR %s"%(nm,str(ex)[:80]))
json.dump(out,open(os.path.join(P,"crypto_hourly.json"),"w"),indent=2,default=str)
lg("DONE coins=%d %.0fs"%(len(out['per_coin']),time.time()-t0))
