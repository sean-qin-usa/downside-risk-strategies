# COMBINED gate (momentum OR misfit) on the 4 gate-profitable ccys (TRY/RUB/IDR/INR), NET OF NDF SPREAD (cost on gate toggles).
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
def series(tk,fld,start,end):
    pdf=to_pd(blp.bdh(tk,fld,start,end))
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vcol=pdf.columns[cols.index('value')]; dcol=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dcol,vcol]].dropna().copy(); s[dcol]=pd.to_datetime(s[dcol],errors='coerce'); return s.dropna(subset=[dcol]).set_index(dcol)[vcol].sort_index().astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
CCY=['TRY','RUB','IDR','INR']; NDF_HALFSPREAD_BP={'TRY':8,'RUB':12,'IDR':15,'INR':6}  # nominal 1M NDF half-spread (bp of notional) fallback
end=dt.date.today(); start=end-dt.timedelta(days=365*16)
def carry_of(spot,fwd):
    df=pd.DataFrame({'spot':spot,'fwd':fwd}).dropna()
    ms=df['spot'].median(); mf=df['fwd'].median(); out=None
    if 0.7*ms<abs(mf)<1.4*ms: out=df['fwd']
    else:
        for s in [1e-4,1e-3,1e-2,1e-1,1.0]:
            cand=df['spot']+df['fwd']*s
            if 0<=float((cand/df['spot']-1).median())<=0.06: out=cand; break
        if out is None: out=df['spot']
    c=(((out/df['spot'])-1)*12).clip(-0.2,1.0); return c if -0.1<=float(c.median())<=1 else pd.Series(0.1,index=df.index)
def SR(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(252)),2) if len(x)>60 and x.std()>0 else np.nan
legs={}
for c in CCY:
    try:
        spot=series(f'USD{c} Curncy','px_last',start,end); fwd=series(f'USD{c}1M Curncy','px_last',start,end)
        if spot is None: lg(f"{c} no spot"); continue
        r=np.log(spot/spot.shift(1)).dropna(); carry=carry_of(spot,fwd).reindex(r.index).ffill() if fwd is not None else pd.Series(0.1,index=r.index)
        # NDF half-spread (of notional) — try bid/ask, else nominal
        try:
            bid=series(f'USD{c}1M Curncy','px_bid',start,end); ask=series(f'USD{c}1M Curncy','px_ask',start,end)
            hs=((ask-bid).abs()/2/spot).reindex(r.index).ffill()
            hsv=float(hs.median());
            if not (0<hsv<0.02): raise ValueError
        except Exception:
            hs=pd.Series(NDF_HALFSPREAD_BP[c]/1e4,index=r.index)
        var=np.empty(len(r)); var[0]=r.var()
        for i in range(1,len(r)): var[i]=0.94*var[i-1]+0.06*r.values[i-1]**2
        z=r/pd.Series(np.sqrt(var),index=r.index).shift(1)
        misfit=(z.abs()>2.5).rolling(15,min_periods=8).mean().shift(1).fillna(0)
        mom=r.rolling(20).sum().shift(1)
        gate=((misfit>0.10)|(mom>0.03)).fillna(False)   # COMBINED
        pos=(~gate).astype(float)
        base=(carry/252.0)-r
        toggle=pos.diff().abs().fillna(pos.abs())        # gate on/off = enter/exit
        cost=toggle*hs                                    # pay half-spread per toggle
        net=base*pos - cost
        legs[c]=dict(ungated=base, gated_net=net, pos=pos, hs=float(pd.Series(hs).median()))
        lg(f"{c}: ungated SR {SR(base)} gated_net SR {SR(net)} | halfspread {float(pd.Series(hs).median())*1e4:.0f}bp | toggles/yr {float(toggle.sum()/ (len(r)/252)):.0f} | costdrag {float(cost.mean()*252*100):.2f}%/yr")
    except Exception as e:
        import traceback; lg(f"{c} ERR {str(e)[:80]}")
# equal-weight basket
if legs:
    ung=pd.concat([legs[c]['ungated'] for c in legs],axis=1).mean(axis=1)
    net=pd.concat([legs[c]['gated_net'] for c in legs],axis=1).mean(axis=1)
    oos_u=ung[ung.index>='2018-01-01']; oos_n=net[net.index>='2018-01-01']
    out={'note':'Combined gate (misfit OR momentum) on TRY/RUB/IDR/INR, NET of NDF half-spread on gate toggles. Equal-weight basket.',
         'per_ccy':{c:dict(ungated_SR=SR(legs[c]['ungated']),gated_net_SR=SR(legs[c]['gated_net']),halfspread_bp=round(legs[c]['hs']*1e4,1)) for c in legs},
         'basket':dict(ungated_SR=SR(ung),gated_net_SR=SR(net),ungated_SR_OOS=SR(oos_u),gated_net_SR_OOS=SR(oos_n),
                       ungated_worst=round(float(ung.min()*100),1),gated_net_worst=round(float(net.min()*100),1))}
    fig,ax=plt.subplots(figsize=(13,5)); ax.plot(ung.index,(1+ung.cumsum()).values,label='ungated carry basket',color='#1f77b4'); ax.plot(net.index,(1+net.cumsum()).values,label='combined-gate, net of NDF spread',color='#2ca02c')
    ax.legend(); ax.set_title("4-currency EM carry basket (TRY/RUB/IDR/INR): ungated vs combined-gate net-of-cost"); ax.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(os.path.join(P,"gate_basket.png"),dpi=110); plt.close()
    json.dump(out,open(os.path.join(P,"gate_basket.json"),"w"),indent=2,default=str)
    lg("BASKET\n"+json.dumps(out['basket'],indent=2))
lg("DONE %.0fs"%(time.time()-t0))
