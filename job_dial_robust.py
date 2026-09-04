# job_dial_robust.py -- four robustness checks on the misspecification dial, one shared panel.
#  (A) DOUBLE-SORT mk63 x rv63 (quintiles): is the score just volatility in disguise?
#      Frontier convention: edge = (GARCH-t pinball - amortized-GBM pinball)/GARCH pinball, 11 taus.
#  (B) SPA (Hansen 2005, consistent p): is any desk model (GARCH-t/FHS/EWMA/HS) superior to the
#      pooled residual-hybrid on per-date mean pinball? Stationary bootstrap blk=10, B=1000.
#  (C) THRESHOLD STABILITY: per-calendar-year 90th percentile of mk63 and that year's top-decile
#      edge (boundary drift = does the dial need recalibration?).
#  (D) CHURN: daily entry rate into the top decile and episode-length stats (production turnover).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
RAWX=['lag1','abs1','prv5','prv21','rv63']
TR=[]; TE=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    # desk-model quantile inputs (causal)
    ztr=z[:cp]
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    for t in [0.5]: pass
    hsq={t: df['y'].rolling(250,min_periods=100).quantile(t).shift(1) for t in TAUS}
    for t in TAUS: df[f'hs_{t}']=hsq[t]
    s2e=pd.Series(y**2).ewm(alpha=0.06,adjust=False).mean().shift(1).values
    df['ewma_sig']=np.sqrt(np.maximum(s2e,1e-8))
    for t in TAUS: df[f'fhs_{t}']=mu+df['sig']*float(np.quantile(ztr,t))
    dd=df.dropna(subset=RAWX+['mk63',f'hs_{TAUS[0]}'])
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TR.append(trn[RAWX+['y']])
    keep=RAWX+['y','sig','date','mu','nu','tsc','mk63','ewma_sig']+[f'hs_{t}' for t in TAUS]+[f'fhs_{t}' for t in TAUS]
    t2=tst[keep].copy(); t2['permno']=pn; TE.append(t2)
lg("panels %d %.0fs"%(len(TE),time.time()-t0))
TRc=pd.concat(TR); TEc=pd.concat(TE).reset_index(drop=True)
GQ={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['y'].values)
    GQ[t]=m.predict(TEc[RAWX].values)
    if t in (0.01,0.5,0.99): lg("  tau %.3f %.0fs"%(t,time.time()-t0))
Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
L={}
L['gbm']=np.mean([pin(Y,GQ[t],t) for t in TAUS],axis=0)
L['garch_t']=np.mean([pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t) for t in TAUS],axis=0)
L['fhs']=np.mean([pin(Y,TEc[f'fhs_{t}'].values,t) for t in TAUS],axis=0)
L['ewma']=np.mean([pin(Y,stats.norm.ppf(t)*TEc['ewma_sig'].values,t) for t in TAUS],axis=0)
L['hs']=np.mean([pin(Y,TEc[f'hs_{t}'].values,t) for t in TAUS],axis=0)
edge=L['garch_t']-L['gbm']
dates=TEc['date'].values; mk=TEc['mk63'].values; rv=TEc['rv63'].values
# ---------- (A) double sort ----------
okA=np.isfinite(mk)&np.isfinite(rv)
qm=pd.qcut(mk[okA],5,labels=False,duplicates='drop'); qr=pd.qcut(rv[okA],5,labels=False,duplicates='drop')
grid=[]
eA=edge[okA]; gA=L['garch_t'][okA]
for i in range(5):
    row=[]
    for j in range(5):
        m5=(qm==i)&(qr==j)
        row.append(round(100*float(eA[m5].mean())/float(gA[m5].mean()),2) if m5.sum()>200 else None)
    grid.append(row)
# key margins: top-mk within each rv quintile, with date-level DM
marg=[]
dA=dates[okA]
for j in range(5):
    m5=(qm==4)&(qr==j)
    if m5.sum()<200: marg.append(None); continue
    s=pd.DataFrame({'d':eA[m5],'date':dA[m5]}).groupby('date')['d'].mean()
    x=s.values; nn=len(x); dmean=x.mean(); v=np.mean((x-dmean)**2)
    for k in range(1,11): v+=2*(1-k/11)*np.mean((x[k:]-dmean)*(x[:-k]-dmean))
    marg.append({'edge_pct':round(100*float(eA[m5].mean())/float(gA[m5].mean()),2),
                 'DM_t':round(float(dmean/math.sqrt(max(v/nn,1e-16))),2),'n':int(m5.sum())})
# ---------- (B) SPA ----------
pl=pd.DataFrame({'date':dates})
for k in L: pl[k]=L[k]
pdm=pl.groupby('date').mean()   # per-date mean loss per model
D=np.column_stack([(pdm[k]-pdm['gbm']).values for k in ['garch_t','fhs','ewma','hs']])  # rival - benchmark; >0 = benchmark better
nT,K=D.shape
dbar=D.mean(axis=0); sd=D.std(axis=0,ddof=1)
tstat=np.sqrt(nT)*dbar/np.maximum(sd,1e-12)
T_spa=max(0.0,float(np.max(-tstat)))   # SPA tests H0: no rival BETTER than benchmark => rival-better means dbar<0
# stationary bootstrap
rng=np.random.default_rng(7); B=1000; blk=10; cnt_ge=0
# Hansen consistent recentering, D-space (D = rival - benchmark, negative = rival better):
# center competitive-or-better rivals (D_bar <= A) at their mean; leave decisive losers uncentered.
A=sd*np.sqrt(2*math.log(math.log(max(nT,3)))/nT)
cvec=np.where(dbar <= A, dbar, 0.0)
for b in range(B):
    idx=[]; i=rng.integers(nT)
    while len(idx)<nT:
        ln=rng.geometric(1.0/blk); idx.extend(((i+np.arange(ln))%nT).tolist()); i=rng.integers(nT)
    idx=np.array(idx[:nT]); Db=D[idx]
    db=Db.mean(axis=0); sb=Db.std(axis=0,ddof=1)
    tb=np.sqrt(nT)*(db-cvec)/np.maximum(sb,1e-12)
    if max(0.0,float(np.max(-tb)))>=T_spa: cnt_ge+=1
p_spa=round(cnt_ge/B,4)
# ---------- (C) threshold stability ----------
yrs=pd.DatetimeIndex(dates).year
stab=[]
thr_all=float(np.nanquantile(mk,0.9))
for yr in sorted(set(yrs)):
    myr=(yrs==yr)&np.isfinite(mk)
    if myr.sum()<5000: continue
    thr=float(np.nanquantile(mk[myr],0.9))
    top=myr&(mk>=thr_all)
    e=round(100*float(edge[top].mean())/float(L['garch_t'][top].mean()),2) if top.sum()>500 else None
    stab.append({'year':int(yr),'q90_mk63':round(thr,2),'top_decile_edge_pct_fixed_thr':e,'n':int(myr.sum())})
# ---------- (D) churn ----------
TEc['top']=(mk>=thr_all).astype(int)
ch=[]
for pn,gg in TEc.groupby('permno'):
    s=gg.sort_values('date')['top'].values
    if len(s)<100: continue
    entries=int(((s[1:]==1)&(s[:-1]==0)).sum())
    runs=[]; c=0
    for v in s:
        if v==1: c+=1
        elif c>0: runs.append(c); c=0
    if c>0: runs.append(c)
    ch.append({'share_top':float(s.mean()),'entries_per_year':252*entries/len(s),'med_run':float(np.median(runs)) if runs else 0})
chd=pd.DataFrame(ch)
OUT={'note':'Dial robustness: (A) mk63 x rv63 quintile double-sort of the GBM-vs-GARCH edge (edge_pct rows=mk63 quintile 1..5, cols=rv63 quintile 1..5); marg = top-mk63 row per rv63 quintile with date-DM. (B) Hansen SPA consistent p of benchmark=pooled GBM vs {garch_t,fhs,ewma,hs}. (C) per-year mk63 90th pct + fixed-threshold top-decile edge. (D) top-decile membership churn.',
     'n_names':int(TEc.permno.nunique()),'n_test':int(len(Y)),
     'A_double_sort_grid':grid,'A_topmk_by_rv_quintile':marg,
     'B_SPA':{'T_spa':round(T_spa,3),'p_consistent':p_spa,'per_rival_t':{k:round(float(t),2) for k,t in zip(['garch_t','fhs','ewma','hs'],tstat)},'note':'positive per-rival t = rival worse than pooled GBM benchmark'},
     'C_threshold_by_year':stab,
     'D_churn':{'mean_share_in_top':round(float(chd['share_top'].mean()),3),'median_entries_per_year':round(float(chd['entries_per_year'].median()),2),'median_run_days':round(float(chd['med_run'].median()),1)}}
json.dump(OUT,open(os.path.join(P,"dial_robust_results.json"),"w"),indent=2)
lg("DIALROBUSTDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=2))
