# MISSPECIFICATION-FRONTIER Bloomberg sweep: which under-researched domains have (a) data on this terminal and
# (b) wild, non-Gaussian distributions (fat tails, jumps, skew) where a parametric GARCH-t template would be misspecified.
import json, os, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
out={'xbbg_ok':False,'series':{}}
try:
    from xbbg import blp
    out['xbbg_ok']=True; lg("xbbg imported")
except Exception as e:
    out['xbbg_import_error']=str(e)[:200]; json.dump(out,open(os.path.join(P,"domain_probe.json"),"w"),indent=2); lg("xbbg import FAIL"); raise SystemExit
import numpy as np, pandas as pd, datetime as dt
TIC={
 # control
 'CTRL_spy':('equity','SPY US Equity'),
 # power / electricity (guesses)
 'POWER_pjm':('power','PJM WEST DA PEAK Index'),'POWER_pjm2':('power','PJMPADAP Index'),
 'POWER_ercot':('power','ERCOTND Index'),'POWER_caiso':('power','CAISO SP15 Index'),
 'POWER_nordpool':('power','ENOSYSPR Index'),'POWER_epexde':('power','ELECDEB Index'),
 # commodities (wild)
 'COMM_natgas':('commodity','NG1 Comdty'),'COMM_crude':('commodity','CL1 Comdty'),'COMM_brent':('commodity','CO1 Comdty'),
 'COMM_gasoline':('commodity','XB1 Comdty'),'COMM_heatoil':('commodity','HO1 Comdty'),'COMM_copper':('commodity','HG1 Comdty'),
 # agriculture
 'AG_corn':('agri','C 1 Comdty'),'AG_wheat':('agri','W 1 Comdty'),'AG_soy':('agri','S 1 Comdty'),
 'AG_coffee':('agri','KC1 Comdty'),'AG_sugar':('agri','SB1 Comdty'),
 # EM FX (devaluation jumps / bimodal)
 'EMFX_try':('emfx','USDTRY Curncy'),'EMFX_ars':('emfx','USDARS Curncy'),'EMFX_brl':('emfx','USDBRL Curncy'),
 'EMFX_zar':('emfx','USDZAR Curncy'),'EMFX_rub':('emfx','USDRUB Curncy'),'EMFX_mxn':('emfx','USDMXN Curncy'),
 # vol indices
 'VOL_vix':('vol','VIX Index'),'VOL_vvix':('vol','VVIX Index'),'VOL_ovx':('vol','OVX Index'),
 'VOL_gvz':('vol','GVZ Index'),'VOL_move':('vol','MOVE Index'),'VOL_skew':('vol','SKEW Index'),
 # credit / rates
 'CREDIT_hyoas':('credit','LF98OAS Index'),'CREDIT_igoas':('credit','LUACOAS Index'),
 'RATES_ust10':('rates','USGG10YR Index'),
 # freight / shipping (spiky)
 'FREIGHT_baltic':('freight','BDIY Index'),
 # crypto
 'CRYPTO_btc':('crypto','XBTUSD Curncy'),'CRYPTO_btc2':('crypto','XBT Curncy'),
}
end=dt.date.today(); start=end-dt.timedelta(days=365*6)
def stats(s):
    s=pd.Series(s).dropna().astype(float)
    r=np.log(s/s.shift(1)).replace([np.inf,-np.inf],np.nan).dropna()
    if len(r)<60: return None
    z=(r-r.mean())/(r.std()+1e-12)
    return dict(rows=int(len(r)), ann_vol=round(float(r.std()*math.sqrt(252)),3),
                kurtosis=round(float(((z**4).mean())-3),1), skew=round(float((z**3).mean()),2),
                jump5sig_pct=round(float((z.abs()>5).mean()*100),3),
                absret_ac1=round(float(r.abs().autocorr(1) if len(r)>5 else np.nan),2),
                worst_day_pct=round(float(r.min()*100),1), best_day_pct=round(float(r.max()*100),1))
for name,(dom,tk) in TIC.items():
    try:
        d=blp.bdh(tk,'PX_LAST',start,end)
        if d is None or not len(d): out['series'][name]={'domain':dom,'ticker':tk,'ok':False,'rows':0}; lg(f"{name} EMPTY"); continue
        col=d.iloc[:,0]; st=stats(col)
        out['series'][name]={'domain':dom,'ticker':tk,'ok':bool(st is not None),**(st or {})}
        lg(f"{name} ({tk}) rows={0 if st is None else st['rows']} kurt={None if st is None else st['kurtosis']}")
    except Exception as e:
        out['series'][name]={'domain':dom,'ticker':tk,'err':str(e)[:100]}; lg(f"{name} ERR {str(e)[:90]}")
# rank available by 'wildness' = kurtosis
avail={k:v for k,v in out['series'].items() if v.get('ok')}
rank=sorted(avail.items(), key=lambda kv: kv[1].get('kurtosis',0), reverse=True)
out['n_available']=len(avail)
out['wildness_ranking']=[{'name':k,'domain':v['domain'],'ticker':v['ticker'],'kurtosis':v.get('kurtosis'),'jump5sig_pct':v.get('jump5sig_pct'),'skew':v.get('skew'),'worst_day_pct':v.get('worst_day_pct')} for k,v in rank]
json.dump(out,open(os.path.join(P,"domain_probe.json"),"w"),indent=2,default=str)
lg("DOMAIN_PROBE_DONE avail=%d %.0fs"%(len(avail),time.time()-t0))
