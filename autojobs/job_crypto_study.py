# FX-OVER-TIME STUDY: nonparametric (IQN-family) vs GARCH-t across USD FX pairs by stability tier, PLUS how the misspecification (edge) evolves over time.
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
def series(tk,start,end):
    pdf=to_pd(blp.bdh(tk,'px_last',start,end))
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vc=pdf.columns[cols.index('value')]; dc=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dc,vc]].dropna().copy(); s[dc]=pd.to_datetime(s[dc],errors='coerce'); return s.dropna(subset=[dc]).set_index(dc)[vc].sort_index().astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
def feats(r):
    d=pd.DataFrame(index=r.index); d['y']=r.values
    d['lag1']=r.shift(1); d['abs1']=r.abs().shift(1)
    d['rv5']=r.rolling(5,min_periods=3).std().shift(1); d['rv21']=r.rolling(21,min_periods=8).std().shift(1)
    d['mean21']=r.rolling(21,min_periods=8).mean().shift(1); d['dn']=(r.shift(1)<0).astype(float)
    return d.dropna()
XC=['lag1','abs1','rv5','rv21','mean21','dn']
def gk(y):
    from arch import arch_model
    try:
        res=arch_model(y,vol='Garch',p=1,o=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        return float(stats.kurtosis(res.std_resid.dropna(),fisher=False))
    except Exception: return None
def h2h(r):
    from arch import arch_model
    D=feats(r); y=D['y'].values; n=len(D); sp=int(n*0.6)
    if n<400: return None
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: return None
    e=y[:sp]-mu; s2=np.empty(len(e)); s2[0]=e.var()
    for k in range(1,len(e)): s2[k]=om+al*e[k-1]**2+be*s2[k-1]
    sig2=s2[-1]; tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    gbm={}
    for t in TAUS:
        m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=150,max_depth=3,learning_rate=0.08); m.fit(D[XC].values[:sp],y[:sp]); gbm[t]=m
    Xte=D[XC].values; gl=nl=0.0; cnt=0
    for i in range(sp,n):
        sig2=om+al*(y[i-1]-mu)**2+be*sig2; sig=math.sqrt(max(sig2,1e-9)); yi=y[i]
        gl+=np.mean([pin(yi,mu+sig*stats.t.ppf(t,nu)/tsc,t) for t in TAUS])
        nl+=np.mean([pin(yi,float(gbm[t].predict(Xte[i:i+1])[0]),t) for t in TAUS]); cnt+=1
    return dict(garch=round(gl/cnt,4),nonparam=round(nl/cnt,4),ratio=round(nl/gl,4),n_oos=cnt)
TIERS={
 'crypto':[('BTC','XBTUSD Curncy'),('ETH','XETUSD Curncy'),('XRP','XRPUSD Curncy'),('LTC','XLCUSD Curncy'),('BCH','XBCUSD Curncy'),('SOL','SOLUSD Curncy'),('DOGE','XDGUSD Curncy')],
}
start=dt.date(2015,1,1); end=dt.date.today()
out={'note':'Crypto study: GBM-quantile (IQN-family) vs GARCH-t on major coins (extreme-instability tier of the stability gradient). ratio=nonparam/garch pinball (<1=nonparam better). resid_kurt=GJR-GARCH-t std-resid kurtosis. Thesis: crypto = biggest nonparam edge + highest resid_kurt of any asset class.','per_coin':{},'summary':{}}
rows=[]
for nm,tk in TIERS['crypto']:
    try:
        s=series(tk,start,end)
        if s is None or len(s)<400: lg("%s NO DATA"%nm); continue
        r=(np.log(s/s.shift(1)).dropna())*100.0
        hh=h2h(r); rk=gk(r.values)
        if hh is None: continue
        rec=dict(start=str(r.index.min().date()),n_days=len(r),ann_vol=round(float(r.std()*np.sqrt(252)),1),worst=round(float(r.min()),1),resid_kurt=round(rk,1) if rk else None,**hh)
        out['per_coin'][nm]=rec; rows.append(rec)
        lg("%-5s ratio %s (g %s/np %s) resid_kurt %s annvol %s  %.0fs"%(nm,hh['ratio'],hh['garch'],hh['nonparam'],rec['resid_kurt'],rec['ann_vol'],time.time()-t0))
        json.dump(out,open(os.path.join(P,"crypto_study.json"),"w"),indent=2,default=str)
    except Exception as ex: lg("%s ERR %s"%(nm,str(ex)[:70]))
if rows:
    rr=[x['ratio'] for x in rows]; rk=[x['resid_kurt'] for x in rows if x['resid_kurt'] is not None]
    out['summary']=dict(n=len(rows),mean_ratio=round(float(np.mean(rr)),4),nonparam_wins=int(sum(1 for x in rr if x<1.0)),mean_resid_kurt=round(float(np.mean(rk)),1) if rk else None,mean_annvol=round(float(np.mean([x['ann_vol'] for x in rows])),1))
json.dump(out,open(os.path.join(P,"crypto_study.json"),"w"),indent=2,default=str)
lg("SUMMARY %s"%json.dumps(out['summary'])); lg("DONE %.0fs"%(time.time()-t0))
