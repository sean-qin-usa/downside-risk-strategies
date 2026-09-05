# job_composite.py -- EVALUATE THE EXACT DEPLOYED SCORE [R20 #1 FATAL].
# Algorithm OA.2 defines the deployed monitor as the decile rank of the MAXIMUM of three
# signals (mk63 kurtosis, |sk63| asymmetry, J5 jump), but the canonical frontier program
# only sorts on each signal separately and the +2.7% headline is mk63 alone. This builds the
# composite ex ante and reports what the desk-deployed object actually does:
#   - individual top-decile edges (mk63, skew63, jump5) for reference
#   - composite as literally defined = max of the three decile ranks; report the max-rank=10
#     set's edge AND occupancy (it is the union of three top deciles, not 10%)
#   - composite as a proper score = max of the three continuous percentiles, re-deciled;
#     full decile profile + top-decile edge/DM/occupancy
#   - causal expanding prior-only 90th-pct cutoff on the composite percentile (as-deployed)
# Engine/panel identical to job_causal_frontier / job_fz_fullpanel (200 names, 11-tau).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
def pin(y,q,t): dd=y-q; return np.where(dd>=0,t*dd,(t-1)*dd)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    dm=x-x.mean(); v=np.mean(dm*dm)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(dm[k:]*dm[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
TRz=[]; rows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        pp=r1.params; om,al,be,mu=float(pp['omega']),float(pp['alpha[1]']),float(pp['beta[1]']),float(pp.get('mu',0)); nu=float(pp.get('nu',8))
    except Exception: continue
    e0=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e0[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); zz=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':zz,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().abs().shift(1)
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=ZX+['mk63','skew63','jump5'])
    trn=dd[dd['idx']<cp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TRz.append(trn[ZX+['z']]); t2=tst.copy(); t2['permno']=pn; rows.append(t2)
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz)
lg("panel %d names %d rows %.0fs"%(TE.permno.nunique(),len(TE),time.time()-t0))
ZQ={}
for t in TAUS:
    ZQ[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06,random_state=0).fit(TRzc[ZX].values,TRzc['z'].values).predict(TE[ZX].values)
    lg("  tau %.3f %.0fs"%(t,time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
plE=np.zeros(len(Y)); plG=np.zeros(len(Y))
for t in TAUS:
    plE+=pin(Y,MU+SIG*ZQ[t],t); plG+=pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t)
plE/=len(TAUS); plG/=len(TAUS)
d=plG-plE
di,udates=pd.factorize(pd.to_datetime(TE['date'].values),sort=True); di=np.asarray(di)
def edge(mask):
    if mask.sum()<30: return None
    g=pd.DataFrame({'d':d[mask],'dt':di[mask]}).groupby('dt')['d'].mean()
    return {'edge_pct':round(100*float(d[mask].mean())/float(plG[mask].mean()),3),'DM':nw_t(g.values),
            'n':int(mask.sum()),'occupancy_pct':round(100*float(mask.mean()),2)}
mk=TE['mk63'].values; sk=TE['skew63'].values; jp=TE['jump5'].values
ok=np.isfinite(mk)&np.isfinite(sk)&np.isfinite(jp)
def dec(x):  # pooled decile rank 1..10 over finite entries; -1 elsewhere
    r=np.full(len(x),-1); m=np.isfinite(x)
    r[m]=pd.qcut(pd.Series(x[m]),10,labels=False,duplicates='drop').values+1
    return r
def pct(x):  # pooled percentile 0..1
    r=np.full(len(x),np.nan); m=np.isfinite(x); r[m]=pd.Series(x[m]).rank(pct=True).values
    return r
rk_mk,rk_sk,rk_jp=dec(mk),dec(sk),dec(jp)
top_mk=rk_mk==10; top_sk=rk_sk==10; top_jp=rk_jp==10
# composite A: literal max of the three decile ranks
comp_maxrank=np.where(ok, np.maximum.reduce([rk_mk,rk_sk,rk_jp]), -1)
maxrank10=comp_maxrank==10                      # union of the three top deciles
# composite B: max of the three continuous percentiles, then re-decile
pct_mk,pct_sk,pct_jp=pct(mk),pct(sk),pct(jp)
comp_pct=np.where(ok, np.fmax.reduce([pct_mk,pct_sk,pct_jp]), np.nan)
cdec=dec(comp_pct)                               # proper deciles of the composite score
# causal expanding prior-only 90th-pct threshold on comp_pct (as-deployed)
BURN=250; by_date={}
for i in range(len(Y)):
    if np.isfinite(comp_pct[i]): by_date.setdefault(di[i],[]).append(comp_pct[i])
prior=[]; seen=0; thr={}
for dd0 in range(len(udates)):
    thr[dd0]=(np.nanpercentile(prior,90) if seen>=BURN else np.nan)
    vs=by_date.get(dd0,[])
    if vs: prior.extend(vs); seen+=1
Bthr=np.array([thr[di[i]] for i in range(len(Y))])
B_top=np.isfinite(Bthr)&np.isfinite(comp_pct)&(comp_pct>=Bthr)
OUT={'note':('Exact Algorithm-OA.2 composite score = rank of the MAX of {mk63, |sk63|, jump5}. '
  'individual_top_deciles: each signal alone. composite_maxrank10 = literal max-of-decile-ranks==10 '
  '(union of the three top deciles; note occupancy>>10%). composite_score_topdecile = top decile of '
  'the re-deciled max-of-percentiles score (a proper 10% cell). causal_expanding = as-deployed prior-only '
  '90th-pct cutoff on the composite percentile. edge=(garch-engine)/garch 11-tau pinball, per-date NW(10).'),
 'n_rows':int(ok.sum()),'n_names':int(TE.permno.nunique()),
 'individual_top_decile':{'mk63':edge(top_mk),'skew63':edge(top_sk),'jump5':edge(top_jp)},
 'composite_maxrank10_union':edge(maxrank10),
 'composite_score_topdecile':edge(cdec==10),
 'composite_score_decile_profile':{int(dd0):edge(cdec==dd0) for dd0 in range(1,11)},
 'composite_causal_expanding_top':edge(B_top),
 'overall':edge(np.ones(len(Y),bool))}
json.dump(OUT,open(os.path.join(P,"composite_results.json"),"w"),indent=2)
lg("COMPOSITEDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1))
