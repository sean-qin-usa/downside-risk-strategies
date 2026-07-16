# TRADEABILITY of the EM-FX misspecification edge: can a lagged regime-gate sidestep devaluation crashes in a carry trade?
# Long-EM carry (short USDXXX) = collect carry, lose on devaluation jumps (short-vol-like). Test if gating improves it.
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
def extract(pdf):
    if pdf is None or not len(pdf): return np.array([])
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols:
        vcol=pdf.columns[cols.index('value')]; dcol=[pdf.columns[i] for i,c in enumerate(cols) if 'date' in c]
        if dcol: pdf=pdf.sort_values(dcol[0])
        return pd.to_numeric(pdf[vcol],errors='coerce').dropna().values.astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().values.astype(float) if num.shape[1] else np.array([])
FX={'USDTRY':('USDTRY Curncy',25.0),'USDMXN':('USDMXN Curncy',8.0),'USDZAR':('USDZAR Curncy',7.0),'USDBRL':('USDBRL Curncy',10.0),'USDARS':('USDARS Curncy',45.0)}
end=dt.date.today(); start=end-dt.timedelta(days=365*11)
def SR(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(252)),2) if len(x)>30 and x.std()>0 else None
out={}
for nm,(tk,carry) in FX.items():
    try:
        vals=extract(to_pd(blp.bdh(tk,'px_last',start,end)))
        if len(vals)<400: out[nm]={'err':'short'}; continue
        fx=pd.Series(vals).astype(float); dl=np.log(fx/fx.shift(1)).replace([np.inf,-np.inf],np.nan)*100  # USDXXX up = EM depreciation
        # long-EM carry daily return = carry/252 - depreciation
        base=(carry/252.0) - dl
        base=base.dropna(); r=dl.reindex(base.index)
        # lagged regime signals (known day before)
        mom20=r.rolling(20).sum().shift(1)   # trailing depreciation trend
        vol21=r.rolling(21).std().shift(1)
        volthr=vol21.quantile(0.80)
        gate_mom = (mom20>3.0)               # depreciating fast -> devaluation regime, stand aside
        gate_vol = (vol21>volthr)
        gate = (gate_mom | gate_vol).fillna(False)
        def bkt(mask_out):
            pos=(~mask_out).astype(float)     # 1 = in market, 0 = flat
            ret=base*pos.reindex(base.index).fillna(1.0)
            return dict(SR=SR(ret), ann_pct=round(float(ret.mean()*252),1), vol_pct=round(float(ret.std()*math.sqrt(252)),1),
                        worst_day=round(float(ret.min()),1), pct_in_mkt=round(float(pos.mean()*100),0))
        out[nm]={'carry_assumed_pct':carry,'n_days':int(len(base)),
                 'UNGATED':bkt(pd.Series(False,index=base.index)),
                 'GATED_mom+vol':bkt(gate)}
        lg(f"{nm}: ungated SR {out[nm]['UNGATED']['SR']} worst {out[nm]['UNGATED']['worst_day']} -> gated SR {out[nm]['GATED_mom+vol']['SR']} worst {out[nm]['GATED_mom+vol']['worst_day']} inmkt {out[nm]['GATED_mom+vol']['pct_in_mkt']}%")
    except Exception as e:
        out[nm]={'err':str(e)[:100]}; lg(f"{nm} ERR {str(e)[:80]}")
out['_note']='Long-EM carry (short USDXXX) with assumed carry. Gate=stand aside when trailing 20d depreciation>3% OR vol in top 20% (lagged). If gated SR>ungated and worst-day less negative, the learnable-regime edge is TRADEABLE. Illustrative carry levels; ARS untradeable in practice (capital controls).'
json.dump(out,open(os.path.join(P,"emfx_trade.json"),"w"),indent=2,default=str)
lg("EMFX_TRADE_DONE %.0fs"%(time.time()-t0))
