# Domain sweep v3 — xbbg returns narwhals/pyarrow; convert to pandas. Bloomberg confirmed live.
import json, os, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
from xbbg import blp
import pandas as pd, numpy as np, datetime as dt
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
        vcol=pdf.columns[cols.index('value')]
        dcol=[pdf.columns[i] for i,c in enumerate(cols) if 'date' in c]
        if dcol: pdf=pdf.sort_values(dcol[0])
        return pd.to_numeric(pdf[vcol],errors='coerce').dropna().values.astype(float)
    num=pdf.select_dtypes('number')
    return num.iloc[:,-1].dropna().values.astype(float) if num.shape[1] else np.array([])
def stats(vals):
    s=pd.Series(vals).dropna().astype(float)
    r=np.log(s/s.shift(1)).replace([np.inf,-np.inf],np.nan).dropna()
    if len(r)<60: return None
    z=(r-r.mean())/(r.std()+1e-12)
    return dict(rows=int(len(r)),ann_vol=round(float(r.std()*math.sqrt(252)),3),kurtosis=round(float((z**4).mean()-3),1),
                skew=round(float((z**3).mean()),2),jump5sig_pct=round(float((z.abs()>5).mean()*100),3),worst_day_pct=round(float(r.min()*100),1))
TIC={'CTRL_spy':('equity','SPY US Equity'),
 'POWER_pjm':('power','PJM WEST DA PEAK Index'),'POWER_ercot':('power','ERCOTND Index'),'POWER_nordpool':('power','ENOSYSPR Index'),'POWER_epex':('power','ELECDEB Index'),
 'COMM_natgas':('commodity','NG1 Comdty'),'COMM_crude':('commodity','CL1 Comdty'),'COMM_gasoline':('commodity','XB1 Comdty'),'COMM_copper':('commodity','HG1 Comdty'),
 'AG_corn':('agri','C 1 Comdty'),'AG_wheat':('agri','W 1 Comdty'),'AG_coffee':('agri','KC1 Comdty'),'AG_sugar':('agri','SB1 Comdty'),
 'EMFX_try':('emfx','USDTRY Curncy'),'EMFX_ars':('emfx','USDARS Curncy'),'EMFX_brl':('emfx','USDBRL Curncy'),'EMFX_zar':('emfx','USDZAR Curncy'),'EMFX_rub':('emfx','USDRUB Curncy'),'EMFX_mxn':('emfx','USDMXN Curncy'),
 'VOL_vix':('vol','VIX Index'),'VOL_ovx':('vol','OVX Index'),'VOL_move':('vol','MOVE Index'),'VOL_gvz':('vol','GVZ Index'),'VOL_vvix':('vol','VVIX Index'),
 'CREDIT_hyoas':('credit','LF98OAS Index'),'CREDIT_igoas':('credit','LUACOAS Index'),'FREIGHT_baltic':('freight','BDIY Index'),'RATES_ust10':('rates','USGG10YR Index'),}
end=dt.date.today(); start=end-dt.timedelta(days=365*6)
out={'series':{}}
for name,(dom,tk) in TIC.items():
    try:
        d=blp.bdh(tk,'px_last',start,end); pdf=to_pd(d); vals=extract(pdf); st=stats(vals)
        out['series'][name]={'domain':dom,'ticker':tk,'ok':bool(st is not None),**(st or {})}
        lg(f"{name} rows={0 if st is None else st['rows']} kurt={None if st is None else st['kurtosis']} jump5%={None if st is None else st['jump5sig_pct']}")
    except Exception as e:
        out['series'][name]={'domain':dom,'ticker':tk,'err':str(e)[:100]}; lg(f"{name} ERR {str(e)[:80]}")
avail={k:v for k,v in out['series'].items() if v.get('ok')}
out['n_available']=len(avail)
out['wildness_ranking']=sorted([{'name':k,'domain':v['domain'],'ticker':v['ticker'],'kurtosis':v.get('kurtosis'),'jump5sig_pct':v.get('jump5sig_pct'),'skew':v.get('skew'),'ann_vol':v.get('ann_vol'),'worst_day_pct':v.get('worst_day_pct')} for k,v in avail.items()],key=lambda x:x['kurtosis'] or 0,reverse=True)
json.dump(out,open(os.path.join(P,"domain3.json"),"w"),indent=2,default=str)
lg("DOMAIN3_DONE avail=%d %.0fs"%(len(avail),time.time()-t0))
