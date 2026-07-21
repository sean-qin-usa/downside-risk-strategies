# AMORTIZATION FLAGSHIP: ONE shared distribution-free quantile model (conditioned on per-name features + static chars)
# vs per-name GARCH-t, evaluated on HELD-OUT names never trained on (transfer). Does the amortized edge GROW on small/young names?
import os, json, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
import numpy as np, pandas as pd
from arch import arch_model
from scipy import stats as sps
from sklearn.ensemble import HistGradientBoostingRegressor
rets=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv")); rets['date']=pd.to_datetime(rets['date']); rets['ret']=pd.to_numeric(rets['ret'],errors='coerce')*100
ch=pd.read_csv(os.path.join(P,"crsp_panel_chars.csv"))
chd={int(r.permno):r for r in ch.itertuples()}
lg("loaded panel %d rows %d names %.0fs"%(len(rets),ch.shape[0],time.time()-t0))
# per-(name) build features
def build(g):
    g=g.sort_values('date'); r=g['ret']
    d=pd.DataFrame({'permno':g['permno'].values,'date':g['date'].values,'y':r.values})
    d['lag1']=r.shift(1).values; d['abs1']=r.abs().shift(1).values; d['rv5']=r.rolling(5).std().shift(1).values
    d['rv21']=r.rolling(21).std().shift(1).values; d['mean21']=r.rolling(21).mean().shift(1).values; d['dn']=(r.shift(1)<0).astype(float).values
    d['age']=np.arange(len(g))  # trading-day age
    return d
parts=[build(g) for _,g in rets.groupby('permno')]
D=pd.concat(parts,ignore_index=True).dropna(subset=['lag1','rv21'])
# attach static chars
D['cohort']=D.permno.map(lambda p: getattr(chd.get(int(p)),'cohort',None))
D['logmcap']=D.permno.map(lambda p: math.log(max(getattr(chd.get(int(p)),'mcap_mm',100) or 100,1)))
D['beta']=D.permno.map(lambda p: getattr(chd.get(int(p)),'beta',None)); D['beta']=pd.to_numeric(D['beta'],errors='coerce').fillna(1.0)
D['sector']=D.permno.map(lambda p: getattr(chd.get(int(p)),'sector',0) or 0)
D['logage']=np.log(D['age']+1)
lg("feature panel %s %.0fs"%(D.shape,time.time()-t0))
# name split: hold out 40% of each cohort (transfer set, NEVER trained)
rng=np.random.default_rng(3); names=ch['permno'].astype(int).values
hold=set()
for c in ['recent_ipo','smallcap','largecap']:
    cn=ch[ch.cohort==c]['permno'].astype(int).values; rng.shuffle(cn); hold|=set(cn[:int(len(cn)*0.4)])
D['held']=D.permno.isin(hold)
tr=D[~D.held]; te=D[D.held]
Xc=['lag1','abs1','rv5','rv21','mean21','dn','logmcap','beta','sector','logage']
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
# ---- amortized model: one HistGBM-quantile per tau, trained on TRAIN names only ----
amq={}
for tau in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=tau,max_iter=200,max_depth=4,learning_rate=0.06,max_leaf_nodes=31)
    m.fit(tr[Xc].values, tr['y'].values); amq[tau]=m
    lg(f"  amort tau {tau} fit {time.time()-t0:.0f}s")
te=te.copy()
for tau in TAUS: te[f'a{tau}']=amq[tau].predict(te[Xc].values)
# ---- per-name GARCH-t on each held-out name's own history ----
def garch_quant(y):
    y=np.asarray(y,dtype=float)
    if len(y)<250: return None
    try:
        am=arch_model(y-y.mean(),mean='Zero',vol='GARCH',p=1,o=1,q=1,dist='t').fit(disp='off')
        pr=am.params; nu=float(pr.get('nu',8)); sig=am.conditional_volatility; mu=float(y.mean()); std=math.sqrt(nu/(nu-2)) if nu>2.05 else 1.0
        return {tau: mu+sig*(sps.t.ppf(tau,nu)/std) for tau in TAUS}
    except Exception: return None
rowsA=[]; rowsG=[]
for pn,g in te.groupby('permno'):
    g=g.sort_values('date'); coh=g['cohort'].iloc[0]
    gq=garch_quant(g['y'].values)
    if gq is None: continue
    y=g['y'].values
    la=np.nanmean([np.nanmean(pin(y,g[f'a{tau}'].values,tau)) for tau in TAUS])
    lg_=np.nanmean([np.nanmean(pin(y,gq[tau],tau)) for tau in TAUS])
    rowsA.append((coh,la)); rowsG.append((coh,lg_))
dfA=pd.DataFrame(rowsA,columns=['cohort','amort']); dfG=pd.DataFrame(rowsG,columns=['cohort','garch'])
out={'n_heldout_names':int(dfA.shape[0]),'note':'amortized HistGBM-quantile (trained on OTHER names, conditioned on features+cap/sector/beta/age) vs per-name GARCH-t (its OWN history). ratio<1 => amortized better. Edge should be biggest on data-starved cohorts.'}
out['by_cohort']={}
for c in ['recent_ipo','smallcap','largecap']:
    a=dfA[dfA.cohort==c]['amort']; gg=dfG[dfG.cohort==c]['garch']
    if len(a)<3: continue
    out['by_cohort'][c]=dict(n=int(len(a)),amort_pinball=round(float(a.mean()),4),garch_pinball=round(float(gg.mean()),4),ratio_amort_over_garch=round(float(a.mean()/gg.mean()),3))
json.dump(out,open(os.path.join(P,"amort_transfer.json"),"w"),indent=2,default=str)
lg("AMORT_TRANSFER\n"+json.dumps(out,indent=2,default=str)); lg("AMORT_DONE %.0fs"%(time.time()-t0))
