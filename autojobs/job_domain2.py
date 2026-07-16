# Bloomberg diagnostic + robust domain sweep. First confirm the terminal returns data, then sweep.
import json, os, time, math, traceback
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
out={'diag':{}}
try:
    from xbbg import blp
    lg("xbbg imported")
except Exception as e:
    out['diag']['import_err']=str(e)[:200]; json.dump(out,open(os.path.join(P,"domain2.json"),"w"),indent=2); raise SystemExit
import pandas as pd, numpy as np, datetime as dt
# ---- DIAGNOSTIC ----
try:
    bdp=blp.bdp('SPY US Equity','px_last'); out['diag']['bdp_type']=str(type(bdp)); out['diag']['bdp_repr']=repr(bdp)[:300]
    lg("bdp SPY: "+repr(bdp)[:150])
except Exception as e:
    out['diag']['bdp_err']=traceback.format_exc()[-400:]; lg("bdp ERR "+str(e)[:150])
try:
    d=blp.bdh('SPY US Equity','px_last',dt.date(2024,1,1),dt.date(2024,3,1))
    out['diag']['bdh_type']=str(type(d)); out['diag']['bdh_shape']=str(getattr(d,'shape',None))
    out['diag']['bdh_cols']=str(list(d.columns))[:200] if hasattr(d,'columns') else 'n/a'
    out['diag']['bdh_head']=repr(d.head())[:400] if hasattr(d,'head') else repr(d)[:300]
    lg("bdh SPY shape="+str(getattr(d,'shape',None)))
except Exception as e:
    out['diag']['bdh_err']=traceback.format_exc()[-500:]; lg("bdh ERR "+str(e)[:150])
bbg_live = out['diag'].get('bdh_shape') not in (None,'None') and 'bdh_err' not in out['diag']
out['bbg_live']=bool(bbg_live)
# ---- SWEEP (only if live) ----
if bbg_live:
    TIC={'CTRL_spy':('equity','SPY US Equity'),
     'POWER_pjm':('power','PJM WEST DA PEAK Index'),'POWER_ercot':('power','ERCOTND Index'),'POWER_nordpool':('power','ENOSYSPR Index'),
     'COMM_natgas':('commodity','NG1 Comdty'),'COMM_crude':('commodity','CL1 Comdty'),'COMM_gasoline':('commodity','XB1 Comdty'),'COMM_copper':('commodity','HG1 Comdty'),
     'AG_corn':('agri','C 1 Comdty'),'AG_wheat':('agri','W 1 Comdty'),'AG_coffee':('agri','KC1 Comdty'),'AG_sugar':('agri','SB1 Comdty'),
     'EMFX_try':('emfx','USDTRY Curncy'),'EMFX_ars':('emfx','USDARS Curncy'),'EMFX_brl':('emfx','USDBRL Curncy'),'EMFX_zar':('emfx','USDZAR Curncy'),'EMFX_rub':('emfx','USDRUB Curncy'),
     'VOL_vix':('vol','VIX Index'),'VOL_ovx':('vol','OVX Index'),'VOL_move':('vol','MOVE Index'),'VOL_gvz':('vol','GVZ Index'),
     'CREDIT_hyoas':('credit','LF98OAS Index'),'FREIGHT_baltic':('freight','BDIY Index'),}
    end=dt.date.today(); start=end-dt.timedelta(days=365*6)
    def stats(vals):
        s=pd.Series(vals).dropna().astype(float)
        r=np.log(s/s.shift(1)).replace([np.inf,-np.inf],np.nan).dropna()
        if len(r)<60: return None
        z=(r-r.mean())/(r.std()+1e-12)
        return dict(rows=int(len(r)),ann_vol=round(float(r.std()*math.sqrt(252)),3),kurtosis=round(float((z**4).mean()-3),1),
                    skew=round(float((z**3).mean()),2),jump5sig_pct=round(float((z.abs()>5).mean()*100),3),
                    worst_day_pct=round(float(r.min()*100),1))
    out['series']={}
    for name,(dom,tk) in TIC.items():
        try:
            d=blp.bdh(tk,'px_last',start,end)
            if not hasattr(d,'shape') or d.shape[0]==0 or d.shape[1]==0:
                out['series'][name]={'domain':dom,'ticker':tk,'ok':False}; lg(f"{name} empty"); continue
            vals=np.asarray(d.iloc[:,0].values,dtype=float); st=stats(vals)
            out['series'][name]={'domain':dom,'ticker':tk,'ok':bool(st is not None),**(st or {})}
            lg(f"{name} rows={0 if st is None else st['rows']} kurt={None if st is None else st['kurtosis']}")
        except Exception as e:
            out['series'][name]={'domain':dom,'ticker':tk,'err':str(e)[:100]}; lg(f"{name} ERR {str(e)[:80]}")
    avail={k:v for k,v in out['series'].items() if v.get('ok')}
    out['n_available']=len(avail)
    out['wildness_ranking']=sorted([{'name':k,'domain':v['domain'],'ticker':v['ticker'],'kurtosis':v.get('kurtosis'),'jump5sig_pct':v.get('jump5sig_pct'),'skew':v.get('skew'),'worst_day_pct':v.get('worst_day_pct')} for k,v in avail.items()],key=lambda x:x['kurtosis'] or 0,reverse=True)
json.dump(out,open(os.path.join(P,"domain2.json"),"w"),indent=2,default=str)
lg("DOMAIN2_DONE bbg_live=%s %.0fs"%(bbg_live,time.time()-t0))
