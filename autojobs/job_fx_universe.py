# BROAD FX UNIVERSE since 1996: momentum-regime-gated carry across ~40 currencies. Which are gate-profitable? Does the rule generalize?
import json, os, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
from xbbg import blp
import numpy as np, pandas as pd, datetime as dt
def to_pd(d):
    for m in ('to_pandas','to_native'):
        if hasattr(d,m):
            try:
                x=getattr(d,m)()
                if hasattr(x,'to_pandas') and not isinstance(x,pd.DataFrame): x=x.to_pandas()
                if isinstance(x,pd.DataFrame): return x
            except Exception: pass
    return d if isinstance(d,pd.DataFrame) else None
def series(tk):
    pdf=to_pd(blp.bdh(tk,'px_last',start,end))
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vcol=pdf.columns[cols.index('value')]; dcol=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dcol,vcol]].dropna().copy(); s[dcol]=pd.to_datetime(s[dcol],errors='coerce'); return s.dropna(subset=[dcol]).set_index(dcol)[vcol].sort_index().astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
CCY=['JPY','CHF','CAD','NOK','SEK','SGD','TRY','ZAR','BRL','MXN','RUB','INR','IDR','CLP','COP','HUF','PLN','CZK','PHP','THB','KRW','TWD','MYR','ILS','RON','EGP','NGN','PKR','KZT','UAH','PEN','AED','SAR','VND','COP','ARS']
CCY=sorted(set(CCY)); start=dt.date(1996,1,1); end=dt.date.today()
def carry_of(spot,fwd):
    df=pd.DataFrame({'spot':spot,'fwd':fwd}).dropna()
    if len(df)<250: return None
    ms=df['spot'].median(); mf=df['fwd'].median(); out=None
    if 0.7*ms<abs(mf)<1.4*ms: out=df['fwd']
    else:
        for s in [1e-5,1e-4,1e-3,1e-2,1e-1,1.0]:
            cand=df['spot']+df['fwd']*s
            if 0<=float((cand/df['spot']-1).median())<=0.06: out=cand; break
        if out is None: return None
    c=(((out/df['spot'])-1)*12).clip(-0.2,1.5)
    return c if -0.1<=float(c.median())<=1.2 else None
def SR(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(252)),2) if len(x)>120 and x.std()>0 else np.nan
per={}; gateprofit=[]; basket_ung=[]; basket_gat=[]
for c in CCY:
    try:
        spot=series(f'USD{c} Curncy')
        if spot is None or len(spot)<300: continue
        fwd=series(f'USD{c}1M Curncy')
        carry=carry_of(spot,fwd) if fwd is not None else None
        r=np.log(spot/spot.shift(1)).dropna()
        if carry is None: carry=pd.Series(np.nan,index=r.index)  # no carry -> spot-only (still test gate on tail)
        carry=carry.reindex(r.index).ffill().fillna(0.0)
        mom=r.rolling(20).sum().shift(1)
        gate=(mom>0.03).fillna(False)                      # causal momentum gate
        base=(carry/252.0)-r; gated=base*(~gate).astype(float)
        ung=SR(base); gat=SR(gated)
        per[c]=dict(start=str(r.index.min().date()),n_days=len(r),median_carry_pct=round(float(carry.median()*100),1),ungated_SR=ung,gated_SR=gat,
                    gate_helps=bool(pd.notna(gat) and pd.notna(ung) and gat-ung>0.2),worst_ung=round(float(base.min()*100),1),worst_gat=round(float(gated.min()*100),1))
        if per[c]['gate_helps']: gateprofit.append(c)
        basket_ung.append(base.rename(c)); basket_gat.append(gated.rename(c))
        lg(f"{c}: {r.index.min().date()} carry {per[c]['median_carry_pct']}% ung {ung} gat {gat} {'GATE-HELPS' if per[c]['gate_helps'] else ''}")
    except Exception as e:
        lg(f"{c} ERR {str(e)[:70]}")
out={'note':'Broad FX universe since 1996. Long-EM carry gated by causal 20d-depreciation-momentum(>3%). gate_helps = gated Sharpe > ungated + 0.2.','n_currencies':len(per),
     'n_gate_profitable':len(gateprofit),'gate_profitable':sorted(gateprofit),'per_currency':per}
if basket_ung:
    U=pd.concat(basket_ung,axis=1).mean(axis=1); G=pd.concat(basket_gat,axis=1).mean(axis=1)
    # gate-profitable subset basket
    if gateprofit:
        Gp=pd.concat([basket_gat[i] for i,c in enumerate([s.name for s in basket_gat]) if c in gateprofit],axis=1).mean(axis=1)
        out['gate_profitable_basket_SR']=SR(Gp)
    out['all_ccy_basket']=dict(ungated_SR=SR(U),gated_SR=SR(G))
json.dump(out,open(os.path.join(P,"fx_universe.json"),"w"),indent=2,default=str)
lg("FX_UNIVERSE done: %d ccys, %d gate-profitable: %s  %.0fs"%(len(per),len(gateprofit),sorted(gateprofit),time.time()-t0))
