# UNIVERSAL CROSS-ASSET + SIGNIFICANCE (host, Bloomberg) — P2 of the plan, LEAN (no slow QR/Markov -> ~10min not 6hr).
# ~43 instruments across every asset class. Per asset: GARCH-t vs FHS vs residual-hybrid (state-conditioned GBM on GARCH
# standardized residuals) + per-date Diebold-Mariano (hybrid vs GARCH) + ES97.5 + post-GARCH residual kurtosis.
# Grouped by asset class. Places every asset class on the misspecification frontier (edge vs resid_kurt).
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
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]; TAIL=[0.005,0.01,0.025]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
def nw_dm(d,lag=10):
    d=np.asarray(d,float); d=d[np.isfinite(d)]; T=len(d)
    if T<30: return None
    dd=d-d.mean(); v=np.mean(dd*dd)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(dd[k:]*dd[:-k])
    if v<=0: return None
    s=d.mean()/math.sqrt(v/T); return dict(DM=round(float(s),2),p=round(float(1-stats.norm.cdf(s)),4))
def analyze(r):
    from arch import arch_model
    y=r.values.astype(float); n=len(y); sp=int(n*0.6)
    if n<600: return None
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: return None
    tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6)
    rk=float(stats.kurtosis(z[:sp][np.isfinite(z[:sp])],fisher=False))
    # residual-state features for the hybrid
    df=pd.DataFrame({'z':z}); df['logsig']=np.log(np.maximum(sig,1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1); df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    ZX=['logsig','zl1','absz5','zstd21']; df['idx']=np.arange(n); dd=df.dropna()
    tr=dd[dd['idx']<sp]; te=dd[dd['idx']>=sp]
    if len(te)<60: return None
    ti=te['idx'].values; yte=y[ti]; sgte=sig[ti]
    fhsq={t:np.quantile(z[:sp],t) for t in TAUS}
    zq={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=150,max_depth=3,learning_rate=0.08).fit(tr[ZX].values,tr['z'].values).predict(te[ZX].values) for t in TAUS}
    Q={'garch_t':{t:mu+sgte*stats.t.ppf(t,nu)/tsc for t in TAUS},'fhs':{t:mu+sgte*fhsq[t] for t in TAUS},'hybrid':{t:mu+sgte*zq[t] for t in TAUS}}
    out={}
    for m in Q:
        pl=np.zeros(len(yte))
        for t in TAUS: pl+=pin(yte,Q[m][t],t)
        pl/=len(TAUS); es=np.mean([Q[m][t] for t in TAIL],axis=0); b99=(yte<Q[m][0.01])
        out[m]=dict(pinball=round(float(pl.mean()),4),ES975=round(float(es.mean()),3),breach99=round(float(b99.mean()),4),_pl=pl)
    # DM: best nonparam (min of fhs,hybrid pinball) vs garch, per-date
    npbest='hybrid' if out['hybrid']['pinball']<=out['fhs']['pinball'] else 'fhs'
    dm=nw_dm(out['garch_t']['_pl']-out[npbest]['_pl'])
    for m in out: out[m].pop('_pl')
    ratio=round(out[npbest]['pinball']/out['garch_t']['pinball'],4)
    return dict(resid_kurt=round(rk,1),garch_pinball=out['garch_t']['pinball'],nonparam_best=npbest,nonparam_pinball=out[npbest]['pinball'],
                ratio=ratio,DM=dm,ES975_garch=out['garch_t']['ES975'],ES975_hybrid=out['hybrid']['ES975'],n_oos=len(yte),per_model=out)
SERIES=[("SPX","SPX Index","equity_index"),("NDX","NDX Index","equity_index"),("AAPL","AAPL US Equity","equity_single"),("XOM","XOM US Equity","equity_single"),
 ("EURUSD","EURUSD Curncy","fx_major"),("USDJPY","USDJPY Curncy","fx_major"),("USDTRY","USDTRY Curncy","fx_em"),("USDBRL","USDBRL Curncy","fx_em"),("USDZAR","USDZAR Curncy","fx_em"),("USDRUB","USDRUB Curncy","fx_em"),
 ("COPPER","HG1 Comdty","commodity"),("CORN","C 1 Comdty","commodity"),("CRUDE","CL1 Comdty","commodity"),("NATGAS","NG1 Comdty","commodity"),("GOLD","GC1 Comdty","commodity"),
 ("PJM_POWER","PW1 Comdty","electricity"),("ERCOT_POWER","ERN1 Comdty","electricity"),("BTC","XBTUSD Curncy","crypto"),("ETH","XETUSD Curncy","crypto"),("VIX","VIX Index","vol"),
 ("US10Y","USGG10YR Index","rates"),("US2Y","USGG2YR Index","rates"),("BUND10Y","GDBR10 Index","rates"),("IG_OAS","LUACOAS Index","credit"),("HY_OAS","LF98OAS Index","credit"),("MOVE","MOVE Index","rates_vol"),
 ("WHEAT","W 1 Comdty","agriculture"),("SOYBEAN","S 1 Comdty","agriculture"),("COFFEE","KC1 Comdty","agriculture"),("SUGAR","SB1 Comdty","agriculture"),("COCOA","CC1 Comdty","agriculture"),("COTTON","CT1 Comdty","agriculture"),
 ("SILVER","SI1 Comdty","metals"),("PLATINUM","PL1 Comdty","metals"),("PALLADIUM","PA1 Comdty","metals"),("ALUMINUM","LA1 Comdty","metals"),("NICKEL","LN1 Comdty","metals"),
 ("BALTIC_DRY","BDIY Index","freight"),("VVIX","VVIX Index","vol"),("V2X","V2X Index","vol"),("HEATING_OIL","HO1 Comdty","energy"),("GASOLINE","XB1 Comdty","energy"),("CARBON_EU","MO1 Comdty","carbon")]
start=dt.date(2005,1,1); end=dt.date.today()
out={'note':'Universal cross-asset + significance (LEAN). Per asset GARCH-t vs FHS vs residual-hybrid (GBM on GARCH std resids) '
            'with per-date Diebold-Mariano (best-nonparam vs GARCH; DM>0&p<.05 => nonparam sig better), ES97.5, resid_kurt. '
            'Grouped by asset class. Places each class on the misspecification frontier (edge vs resid_kurt).','per_asset':{},'by_class':{}}
pairs=[]
for nm,tk,cls in SERIES:
    try:
        s=series(tk,start,end)
        if s is None or len(s)<600: lg("%s NO DATA (%s)"%(nm,tk)); continue
        r=(s.diff().dropna()) if ('Index' in tk and ('YR' in tk or 'OAS' in tk or tk.startswith('GDBR'))) else (np.log(s/s.shift(1)).dropna())
        r=r*100.0; a=analyze(r)
        if a is None: lg("%s SKIP"%nm); continue
        a['class']=cls; a.pop('per_model'); out['per_asset'][nm]=a
        dmv=a['DM']['DM'] if isinstance(a['DM'],dict) and a['DM'].get('DM') is not None else None
        if a['resid_kurt'] is not None and dmv is not None: pairs.append((a['resid_kurt'],a['garch_pinball']-a['nonparam_pinball']))
        lg("%-12s [%s] ratio %s DM %s rkurt %s  %.0fs"%(nm,cls,a['ratio'],a['DM'],a['resid_kurt'],time.time()-t0))
        json.dump(out,open(os.path.join(P,"universal_sig.json"),"w"),indent=2,default=str)
    except Exception as ex: lg("%s ERR %s"%(nm,str(ex)[:70]))
# by class
cls_map={}
for nm,rec in out['per_asset'].items(): cls_map.setdefault(rec['class'],[]).append(rec)
for cls,recs in cls_map.items():
    rr=[x['ratio'] for x in recs]; rk=[x['resid_kurt'] for x in recs if x['resid_kurt'] is not None]
    sig=sum(1 for x in recs if isinstance(x['DM'],dict) and x['DM'].get('DM') is not None and x['DM']['DM']>1.64)
    out['by_class'][cls]=dict(n=len(recs),mean_ratio=round(float(np.mean(rr)),4),nonparam_wins=int(sum(1 for x in rr if x<1.0)),sig_wins=int(sig),mean_resid_kurt=round(float(np.mean(rk)),1) if rk else None)
if len(pairs)>=8:
    rk_a=np.array([a for a,_ in pairs]); ed_a=np.array([b for _,b in pairs])
    out['edge_vs_logresidkurt_corr']=round(float(np.corrcoef(np.log(np.clip(rk_a,1,None)),ed_a)[0,1]),3)
n_sig=sum(1 for x in out['per_asset'].values() if isinstance(x['DM'],dict) and x['DM'].get('DM') is not None and x['DM']['DM']>1.64)
out['n_assets']=len(out['per_asset']); out['n_nonparam_sig_wins']=int(n_sig)
json.dump(out,open(os.path.join(P,"universal_sig.json"),"w"),indent=2,default=str)
lg("BY CLASS:\n"+json.dumps(out['by_class'],indent=2)); lg("corr(log rkurt,edge)=%s  sig_wins=%d/%d  %.0fs"%(out.get('edge_vs_logresidkurt_corr'),n_sig,out['n_assets'],time.time()-t0))
