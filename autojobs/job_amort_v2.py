# AMORTIZATION v2: credit COLD-START (GARCH can't fit) + show edge grows as history shrinks. Bucket held-out names by history length.
import os, json, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
import numpy as np, pandas as pd
from arch import arch_model
from scipy import stats as sps
from sklearn.ensemble import HistGradientBoostingRegressor
rets=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv")); rets['date']=pd.to_datetime(rets['date']); rets['ret']=pd.to_numeric(rets['ret'],errors='coerce')*100
ch=pd.read_csv(os.path.join(P,"crsp_panel_chars.csv")); chd={int(r.permno):r for r in ch.itertuples()}
def build(g):
    g=g.sort_values('date'); r=g['ret']; d=pd.DataFrame({'permno':g['permno'].values,'date':g['date'].values,'y':r.values})
    d['lag1']=r.shift(1).values; d['abs1']=r.abs().shift(1).values; d['rv5']=r.rolling(5).std().shift(1).values
    d['rv21']=r.rolling(21).std().shift(1).values; d['rv63']=r.rolling(63,min_periods=20).std().shift(1).values
    d['mean21']=r.rolling(21).mean().shift(1).values; d['dn']=(r.shift(1)<0).astype(float).values; d['age']=np.arange(len(g))
    return d
D=pd.concat([build(g) for _,g in rets.groupby('permno')],ignore_index=True).dropna(subset=['lag1','rv21'])
D['cohort']=D.permno.map(lambda p: getattr(chd.get(int(p)),'cohort',None))
D['logmcap']=D.permno.map(lambda p: math.log(max(getattr(chd.get(int(p)),'mcap_mm',100) or 100,1)))
D['beta']=pd.to_numeric(D.permno.map(lambda p: getattr(chd.get(int(p)),'beta',None)),errors='coerce').fillna(1.0)
D['sector']=D.permno.map(lambda p: getattr(chd.get(int(p)),'sector',0) or 0)
D['logage']=np.log(D['age']+1); D['rv63']=D['rv63'].fillna(D['rv21'])
rng=np.random.default_rng(3); hold=set()
for c in ['recent_ipo','smallcap','largecap']:
    cn=ch[ch.cohort==c]['permno'].astype(int).values; rng.shuffle(cn); hold|=set(cn[:int(len(cn)*0.4)])
D['held']=D.permno.isin(hold); tr=D[~D.held]; te=D[D.held]
Xc=['lag1','abs1','rv5','rv21','rv63','mean21','dn','logmcap','beta','sector','logage']
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
amq={}
for tau in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=tau,max_iter=250,max_depth=4,learning_rate=0.06,max_leaf_nodes=31)
    m.fit(tr[Xc].values,tr['y'].values); amq[tau]=m
lg("amort fit %.0fs"%(time.time()-t0))
te=te.copy()
for tau in TAUS: te[f'a{tau}']=amq[tau].predict(te[Xc].values)
def garch_q(y):
    y=np.asarray(y,float)
    if len(y)<250: return None
    try:
        am=arch_model(y-y.mean(),mean='Zero',vol='GARCH',p=1,o=1,q=1,dist='t').fit(disp='off')
        nu=float(am.params.get('nu',8)); sig=am.conditional_volatility; mu=float(y.mean()); std=math.sqrt(nu/(nu-2)) if nu>2.05 else 1.0
        return {tau:mu+sig*(sps.t.ppf(tau,nu)/std) for tau in TAUS}
    except Exception: return None
# per held-out name: history length, amortized pinball, garch pinball (or None=cold-start), amortized p05 breach (calibration)
rows=[]
for pn,g in te.groupby('permno'):
    g=g.sort_values('date'); y=g['y'].values; hist=len(g); coh=g['cohort'].iloc[0]
    la=float(np.nanmean([np.nanmean(pin(y,g[f'a{tau}'].values,tau)) for tau in TAUS]))
    br05=float((y<g['a0.05'].values).mean())  # amortized 5% coverage
    gq=garch_q(y); lg_= float(np.nanmean([np.nanmean(pin(y,gq[tau],tau)) for tau in TAUS])) if gq else None
    rows.append(dict(permno=int(pn),cohort=coh,hist=hist,amort=la,garch=lg_,coldstart=(gq is None),amort_p05_breach=br05))
df=pd.DataFrame(rows)
out={'n_heldout':len(df),'note':'Amortized quantile model on UNSEEN names. Bucketed by history length. Cold-start = GARCH cannot fit (<250 usable days): amortized is the ONLY option there (capability, not accuracy).'}
# cold-start capability
cs=df[df.coldstart]
out['cold_start']=dict(n=int(len(cs)), pct_of_heldout=round(float(len(cs)/len(df)*100),1),
    by_cohort={c:int((cs.cohort==c).sum()) for c in ['recent_ipo','smallcap','largecap']},
    amort_avg_pinball=round(float(cs.amort.mean()),4) if len(cs) else None,
    amort_p05_breach=round(float(cs.amort_p05_breach.mean()),3) if len(cs) else None,
    garch_pinball='N/A (cannot fit)')
# history-length buckets (where GARCH CAN fit): does amort edge grow as history shrinks?
fit=df[~df.coldstart].copy(); fit['bucket']=pd.cut(fit['hist'],[0,500,1000,2000,99999],labels=['250-500d','500-1000d','1000-2000d','>2000d'])
out['by_history_bucket']={}
for b,gg in fit.groupby('bucket',observed=True):
    if len(gg)<3: continue
    out['by_history_bucket'][str(b)]=dict(n=int(len(gg)),amort=round(float(gg.amort.mean()),4),garch=round(float(gg.garch.mean()),4),ratio=round(float(gg.amort.mean()/gg.garch.mean()),3))
json.dump(out,open(os.path.join(P,"amort_v2.json"),"w"),indent=2,default=str)
lg("AMORT_V2\n"+json.dumps(out,indent=2,default=str)); lg("DONE %.0fs"%(time.time()-t0))
