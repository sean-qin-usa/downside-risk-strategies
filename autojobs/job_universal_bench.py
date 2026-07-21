# UNIVERSAL-MODEL BENCHMARK: is the distribution-free IQN-family (GBM quantile) competitive with each domain's FLAGSHIP model, across every asset class we can source?
# Models per series: own-empirical (floor) | GARCH-t | GARCH-EVT | QR (QRA stand-in) | Markov-switching | GBM (IQN stand-in)
# Metric: avg pinball over 7 taus, walk-forward OOS. Reports per-series winner + IQN gap-to-best, and a universality score.
import json, os, time, math, warnings
warnings.filterwarnings("ignore")
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
import numpy as np, pandas as pd, datetime as dt
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
def to_pd(d):
    for m in ('to_pandas','to_native'):
        if hasattr(d,m):
            try:
                x=getattr(d,m)()
                if hasattr(x,'to_pandas') and not isinstance(x,pd.DataFrame): x=x.to_pandas()
                if isinstance(x,pd.DataFrame): return x
            except Exception: pass
    return d if isinstance(d,pd.DataFrame) else None
def bbg_series(tk,start,end):
    from xbbg import blp
    pdf=to_pd(blp.bdh(tk,'px_last',start,end))
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vcol=pdf.columns[cols.index('value')]; dcol=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dcol,vcol]].dropna().copy(); s[dcol]=pd.to_datetime(s[dcol],errors='coerce'); return s.dropna(subset=[dcol]).set_index(dcol)[vcol].sort_index().astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
# ---- domain map: (name, ticker, domain, flagship) ----
SERIES=[
 ("SPX","SPX Index","equity_index","garch_t"),
 ("NDX","NDX Index","equity_index","garch_t"),
 ("AAPL","AAPL US Equity","equity_single","garch_t"),
 ("XOM","XOM US Equity","equity_single","garch_t"),
 ("EURUSD","EURUSD Curncy","fx_major","garch_t"),
 ("USDJPY","USDJPY Curncy","fx_major","garch_t"),
 ("USDTRY","USDTRY Curncy","fx_em","markov"),
 ("USDBRL","USDBRL Curncy","fx_em","markov"),
 ("USDZAR","USDZAR Curncy","fx_em","markov"),
 ("USDRUB","USDRUB Curncy","fx_em","markov"),
 ("COPPER","HG1 Comdty","commodity","garch_t"),
 ("CORN","C 1 Comdty","commodity","garch_t"),
 ("CRUDE","CL1 Comdty","commodity","garch_t"),
 ("NATGAS","NG1 Comdty","commodity","garch_t"),
 ("GOLD","GC1 Comdty","commodity","garch_t"),
 ("PJM_POWER","PW1 Comdty","electricity","qr"),
 ("ERCOT_POWER","ERN1 Comdty","electricity","qr"),
 ("BTC","XBTUSD Curncy","crypto","garch_t"),
 ("ETH","XETUSD Curncy","crypto","garch_t"),
 ("VIX","VIX Index","vol","garch_t"),
 # --- expanded industry breadth (Bloomberg-sourced) ---
 ("US10Y","USGG10YR Index","rates","garch_t"),
 ("US2Y","USGG2YR Index","rates","garch_t"),
 ("BUND10Y","GDBR10 Index","rates","garch_t"),
 ("IG_OAS","LUACOAS Index","credit","garch_t"),
 ("HY_OAS","LF98OAS Index","credit","garch_t"),
 ("MOVE","MOVE Index","rates_vol","garch_t"),
 ("WHEAT","W 1 Comdty","agriculture","garch_t"),
 ("SOYBEAN","S 1 Comdty","agriculture","garch_t"),
 ("COFFEE","KC1 Comdty","agriculture","garch_t"),
 ("SUGAR","SB1 Comdty","agriculture","garch_t"),
 ("COCOA","CC1 Comdty","agriculture","garch_t"),
 ("COTTON","CT1 Comdty","agriculture","garch_t"),
 ("SILVER","SI1 Comdty","metals","garch_t"),
 ("PLATINUM","PL1 Comdty","metals","garch_t"),
 ("PALLADIUM","PA1 Comdty","metals","garch_t"),
 ("ALUMINUM","LA1 Comdty","metals","garch_t"),
 ("NICKEL","LN1 Comdty","metals","garch_t"),
 ("BALTIC_DRY","BDIY Index","freight","garch_t"),
 ("VVIX","VVIX Index","vol","garch_t"),
 ("V2X","V2X Index","vol","garch_t"),
 ("GAS_UK","NBP1 Comdty","energy_gas","garch_t"),
 ("HEATING_OIL","HO1 Comdty","energy","garch_t"),
 ("GASOLINE","XB1 Comdty","energy","garch_t"),
 ("CARBON_EU","MO1 Comdty","carbon","garch_t"),
]
start=dt.date(2005,1,1); end=dt.date.today()
def feats(r):
    d=pd.DataFrame(index=r.index); d['y']=r.values
    d['lag1']=r.shift(1); d['abs1']=r.abs().shift(1)
    d['rv5']=r.rolling(5,min_periods=3).std().shift(1); d['rv21']=r.rolling(21,min_periods=8).std().shift(1)
    d['mean21']=r.rolling(21,min_periods=8).mean().shift(1); d['dn']=(r.shift(1)<0).astype(float)
    return d.dropna()
XC=['lag1','abs1','rv5','rv21','mean21','dn']
def garch_params(r):
    from arch import arch_model
    am=arch_model(r,vol='Garch',p=1,q=1,dist='t',rescale=False)
    res=am.fit(disp='off',show_warning=False)
    p=res.params; nu=p.get('nu',8.0); mu=p.get('mu',0.0)
    return float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(nu),float(mu),res
def run_series(name,r,flagship):
    r=r.dropna()*100.0
    if len(r)<800: return {'note':'insufficient','n':len(r)}
    D=feats(r); y=D['y'].values; n=len(D); split=int(n*0.6); K=20; K2=60
    oos=range(split,n); res={m:[] for m in ['own','garch_t','garch_evt','qr','markov','gbm']}
    # ---- GBM & QR: refit every K2 ----
    gbm_models={}; qr_models={}
    def refit_ml(i):
        Xtr=D[XC].values[:i]; ytr=y[:i]
        for tau in TAUS:
            try:
                m=HistGradientBoostingRegressor(loss='quantile',quantile=tau,max_iter=150,max_depth=3,learning_rate=0.07); m.fit(Xtr,ytr); gbm_models[tau]=m
            except Exception: gbm_models[tau]=None
        try:
            import statsmodels.formula.api as smf
            dd=pd.DataFrame(Xtr,columns=XC); dd['y']=ytr
            for tau in TAUS:
                try: qr_models[tau]=smf.quantreg('y ~ '+'+'.join(XC),dd).fit(q=tau)
                except Exception: qr_models[tau]=None
        except Exception:
            for tau in TAUS: qr_models[tau]=None
    # ---- GARCH: refit every K, roll variance recursion between ----
    gp=None; sig2=None
    def refit_garch(i):
        nonlocal gp,sig2
        try:
            gp=garch_params(y[:i]); om,al,be,nu,mu,_=gp
            e=y[:i]-mu; s2=np.empty(len(e)); s2[0]=e.var()
            for k in range(1,len(e)): s2[k]=om+al*e[k-1]**2+be*s2[k-1]
            sig2=s2[-1]
        except Exception: gp=None
    # ---- Markov: fit once on training ----
    mk=None
    try:
        import statsmodels.api as sm
        mm=sm.tsa.MarkovRegression(y[:split],k_regimes=2,trend='c',switching_variance=True).fit()
        mk=(float(mm.params[-2]),float(mm.params[-1]),mm)  # two variances (approx)
    except Exception: mk=None
    refit_ml(split); refit_garch(split)
    evt_lower=None
    if gp is not None:
        om,al,be,nu,mu,_=gp; z=(y[:split]-mu)/np.sqrt(np.maximum(sig2,1e-9))
        try:
            thr=np.quantile(z,0.10); tail=thr-z[z<thr]
            if len(tail)>30: evt_lower=(thr,*stats.genpareto.fit(tail[tail>0]))
        except Exception: evt_lower=None
    for j,i in enumerate(oos):
        yi=y[i]; own_hist=y[max(0,i-750):i]
        # own-empirical
        res['own'].append(np.mean([pin(yi,np.quantile(own_hist,tau),tau) for tau in TAUS]))
        # GBM
        if any(gbm_models.get(t) is not None for t in TAUS):
            res['gbm'].append(np.mean([pin(yi,float(gbm_models[t].predict(D[XC].values[i:i+1])[0]),t) for t in TAUS if gbm_models.get(t) is not None]))
        # QR
        if any(qr_models.get(t) is not None for t in TAUS):
            xrow=pd.DataFrame(D[XC].values[i:i+1],columns=XC)
            res['qr'].append(np.mean([pin(yi,float(qr_models[t].predict(xrow)[0]),t) for t in TAUS if qr_models.get(t) is not None]))
        # GARCH-t + EVT (roll variance)
        if gp is not None:
            om,al,be,nu,mu,_=gp
            sig2=om+al*(y[i-1]-mu)**2+be*sig2; sig=math.sqrt(max(sig2,1e-9)); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
            res['garch_t'].append(np.mean([pin(yi,mu+sig*stats.t.ppf(tau,nu)/tsc,tau) for tau in TAUS]))
            def evtq(tau):
                if tau<=0.05 and evt_lower is not None:
                    thr,c,loc,scl=evt_lower; p_exc=stats.genpareto.ppf(1-tau/0.10,c,loc,scl); return mu+sig*(thr-p_exc)
                return mu+sig*stats.t.ppf(tau,nu)/tsc
            res['garch_evt'].append(np.mean([pin(yi,evtq(tau),tau) for tau in TAUS]))
        # Markov (fixed regimes, unconditional mixture)
        if mk is not None:
            v1,v2,_=mk; mu2=np.mean(y[:split]); sig=math.sqrt(max((abs(v1)+abs(v2))/2,1e-9))
            res['markov'].append(np.mean([pin(yi,mu2+sig*stats.norm.ppf(tau),tau) for tau in TAUS]))
        if (j+1)%K2==0: refit_ml(i)
        if (j+1)%K==0: refit_garch(i)
    out={'domain':None,'n':n,'n_oos':len(list(oos))}
    for m in res: out[m]=round(float(np.mean(res[m])),4) if res[m] else None
    valid={m:out[m] for m in ['own','garch_t','garch_evt','qr','markov','gbm'] if out[m] is not None}
    if valid:
        best=min(valid,key=valid.get); out['best_model']=best; out['best_pinball']=valid[best]
        out['flagship']=flagship; out['flagship_pinball']=out.get(flagship)
        if out.get('gbm') is not None:
            out['gbm_gap_to_best_pct']=round((out['gbm']/valid[best]-1)*100,2)
            fl=out.get(flagship) or out.get('garch_t')
            out['gbm_vs_flagship_pct']=round((out['gbm']/fl-1)*100,2) if fl else None
            out['gbm_wins']=bool(best=='gbm')
    return out
RESULT={}
for name,tk,domain,flag in SERIES:
    try:
        s=bbg_series(tk,start,end)
        if s is None: lg(f"{name}: NO DATA ({tk})"); RESULT[name]={'note':'no data','ticker':tk,'domain':domain}; continue
        r=np.log(s/s.shift(1)).dropna()
        o=run_series(name,r,flag); o['domain']=domain; o['ticker']=tk; RESULT[name]=o
        lg(f"{name} [{domain}] gbm={o.get('gbm')} best={o.get('best_model')}({o.get('best_pinball')}) flag={flag}({o.get('flagship_pinball')}) gap_to_best={o.get('gbm_gap_to_best_pct')}% {'WIN' if o.get('gbm_wins') else ''}  {time.time()-t0:.0f}s")
        json.dump(RESULT,open(os.path.join(P,"universal_bench.json"),"w"),indent=2,default=str)  # incremental
    except Exception as e:
        import traceback; lg(f"{name} ERR {str(e)[:100]}"); RESULT[name]={'err':str(e)[:120],'ticker':tk}
# ---- universality summary ----
comp={'within_2pct_of_best':[],'within_5pct_of_best':[],'gbm_wins':[],'lags_gt5pct':[]}
for name,o in RESULT.items():
    g=o.get('gbm_gap_to_best_pct')
    if g is None: continue
    if o.get('gbm_wins'): comp['gbm_wins'].append(name)
    if g<=2.0: comp['within_2pct_of_best'].append(name)
    if g<=5.0: comp['within_5pct_of_best'].append(name)
    if g>5.0: comp['lags_gt5pct'].append(name)
n_scored=sum(1 for o in RESULT.values() if o.get('gbm_gap_to_best_pct') is not None)
summary={'note':'IQN-family (GBM quantile) vs domain flagship across asset classes. gbm_gap_to_best_pct = how far IQN is from the single best model (0 = IQN is best). Universality = fraction of domains where IQN is within X% of the best.',
         'n_series_scored':n_scored,'universality_within_2pct':f"{len(comp['within_2pct_of_best'])}/{n_scored}",'universality_within_5pct':f"{len(comp['within_5pct_of_best'])}/{n_scored}",
         'gbm_outright_wins':comp['gbm_wins'],'within_2pct':comp['within_2pct_of_best'],'within_5pct':comp['within_5pct_of_best'],'lags_gt5pct':comp['lags_gt5pct']}
RESULT['_UNIVERSALITY_SUMMARY']=summary
json.dump(RESULT,open(os.path.join(P,"universal_bench.json"),"w"),indent=2,default=str)
lg("UNIVERSALITY: within2%="+summary['universality_within_2pct']+" within5%="+summary['universality_within_5pct']+" wins="+str(comp['gbm_wins']))
lg("DONE %.0fs"%(time.time()-t0))
