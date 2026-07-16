# AUTO CRISIS-REGIME DETECTION (causal, no future info) via MULTIPLE signals -> which currencies' FX carry is gate-profitable?
# Signals (all lagged/past-only): model-misfit, vol-level, depreciation-momentum, vol-acceleration, combined. Backtest each; rank; select tradeable ccys.
import json, os, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
from xbbg import blp
import numpy as np, pandas as pd, datetime as dt
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
def to_pd(d):
    for m in ('to_pandas','to_native'):
        if hasattr(d,m):
            try:
                x=getattr(d,m)()
                if hasattr(x,'to_pandas') and not isinstance(x,pd.DataFrame): x=x.to_pandas()
                if isinstance(x,pd.DataFrame): return x
            except Exception: pass
    return d if isinstance(d,pd.DataFrame) else None
def extract_d(pdf):
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vcol=pdf.columns[cols.index('value')]; dcol=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dcol,vcol]].dropna().copy(); s[dcol]=pd.to_datetime(s[dcol],errors='coerce'); s=s.dropna(subset=[dcol])
        return s.set_index(dcol)[vcol].sort_index().astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
def carry_of(c,start,end):
    spot=extract_d(to_pd(blp.bdh(f'USD{c} Curncy','px_last',start,end))); fwd=extract_d(to_pd(blp.bdh(f'USD{c}1M Curncy','px_last',start,end)))
    if spot is None or len(spot)<500: return None,None
    df=pd.DataFrame({'spot':spot});
    if fwd is not None: df['fwd']=fwd
    df=df.dropna()
    if 'fwd' not in df: return df['spot'],pd.Series(0.1,index=df.index)
    ms=df['spot'].median(); mf=df['fwd'].median(); out=None
    if 0.7*ms<abs(mf)<1.4*ms: out=df['fwd']
    else:
        for s in [1e-4,1e-3,1e-2,1e-1,1.0]:
            cand=df['spot']+df['fwd']*s
            if 0<=float((cand/df['spot']-1).median())<=0.06: out=cand; break
        if out is None: out=df['spot']
    carry=(((out/df['spot'])-1)*12).clip(-0.2,1.0)
    if not -0.1<=float(carry.median())<=1: carry=pd.Series(0.1,index=df.index)
    return df['spot'],carry
def SR(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(252)),2) if len(x)>60 and x.std()>0 else np.nan
def signals(r):
    # all CAUSAL (lagged). r=log returns of USDXXX (up=EM depreciation)
    var=np.empty(len(r)); var[0]=r.var(); rr=r.values
    for i in range(1,len(r)): var[i]=0.94*var[i-1]+0.06*rr[i-1]**2
    sig=pd.Series(np.sqrt(var),index=r.index); z=r/sig.shift(1)
    misfit=(z.abs()>2.5).rolling(15,min_periods=8).mean().shift(1).fillna(0)     # model-misfit
    vol60=r.rolling(60).std().shift(1); volhigh=(vol60>vol60.expanding(250).quantile(0.80)).fillna(False)  # turbulence
    mom=(r.rolling(20).sum().shift(1)>0.03).fillna(False)                          # depreciation momentum
    volaccel=((r.rolling(10).std().shift(1))/(r.rolling(60).std().shift(1)+1e-9)>1.5).fillna(False)  # vol rising fast
    return dict(misfit=(misfit>0.10),volhigh=volhigh,momentum=mom,volaccel=volaccel,
                combined=((misfit>0.10)|volhigh|mom|volaccel))
CCY=['TRY','RUB','ZAR','MXN','BRL','IDR','INR','CLP']; end=dt.date.today(); start=end-dt.timedelta(days=365*14)
SIGS=['misfit','volhigh','momentum','volaccel','combined']; out={'note':'Causal crisis-regime signals gating long-EM carry. ratio of gated/ungated Sharpe; which currencies are gate-profitable (gating lifts Sharpe).','signals':SIGS}
per={}; charts=[]; gateprofit={s:[] for s in SIGS}
for c in CCY:
    try:
        spot,carry=carry_of(c,start,end)
        if spot is None: continue
        r=np.log(spot/spot.shift(1)).dropna(); carry=carry.reindex(r.index).ffill(); base=(carry/252.0)-r
        S=signals(r); ung=SR(base); cell={'ungated_SR':ung,'ungated_worst':round(float(base.min()*100),1)}
        for s in SIGS:
            g=S[s].reindex(base.index).fillna(False); gated=base*(~g).astype(float)
            cell[s+'_SR']=SR(gated); cell[s+'_worst']=round(float(gated.min()*100),1); cell[s+'_inmkt']=round(float((~g).mean()*100),0)
            if pd.notna(cell[s+'_SR']) and pd.notna(ung) and cell[s+'_SR']-ung>0.2: gateprofit[s].append(c)
        per[c]=cell
        best=max(SIGS,key=lambda s: (cell.get(s+'_SR') if pd.notna(cell.get(s+'_SR')) else -9))
        lg(f"{c}: ungated {ung} | "+" ".join(f"{s}={cell[s+'_SR']}" for s in SIGS)+f" | best={best}")
        if c in ('TRY','RUB'):
            g=S['combined'].reindex(spot.index).fillna(False).values; fig,ax=plt.subplots(2,1,figsize=(13,7),sharex=True)
            fig.suptitle(f"USD{c}: causal crisis-regime (combined signal, red) + carry equity",weight='bold')
            lp=np.log(spot.values); ax[0].plot(spot.index,lp,color='k',lw=.8); ax[0].fill_between(spot.index,lp.min(),lp.max(),where=g,color='red',alpha=.15); ax[0].set_title(f"log USD{c}  (red = auto-flagged crisis regime)"); ax[0].grid(alpha=.3)
            equ=(1+base.cumsum()); ga=base*(~S['combined'].reindex(base.index).fillna(False)).astype(float); eqa=(1+ga.cumsum())
            ax[1].plot(equ.index,equ.values,label='ungated carry',color='#1f77b4'); ax[1].plot(eqa.index,eqa.values,label='auto-gated (combined)',color='#2ca02c'); ax[1].legend(); ax[1].set_title("cumulative long-EM carry"); ax[1].grid(alpha=.3)
            f=os.path.join(P,f"regime_{c}.png"); plt.tight_layout(rect=[0,0,1,.96]); plt.savefig(f,dpi=110); plt.close(); charts.append(f)
    except Exception as e:
        import traceback; lg(f"{c} ERR {str(e)[:80]}"); per[c]={'err':str(e)[:90]}
out['per_currency']=per; out['gate_profitable_currencies_by_signal']=gateprofit; out['charts']=charts
json.dump(out,open(os.path.join(P,"regime_detector.json"),"w"),indent=2,default=str)
lg("GATE-PROFITABLE by signal:\n"+json.dumps(gateprofit,indent=2)); lg("REGIME_DONE %.0fs"%(time.time()-t0))
