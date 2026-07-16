# Electricity data probe: confirm Bloomberg terminal live + entitlement, discover power tickers. Fallback notes only.
import json, os, time
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
out={'xbbg_ok':False,'tickers':{}}
try:
    from xbbg import blp
    out['xbbg_ok']=True; lg("xbbg imported")
except Exception as e:
    out['xbbg_import_error']=str(e)[:200]; json.dump(out,open(os.path.join(P,"power_probe.json"),"w"),indent=2); lg("xbbg import FAIL "+str(e)[:150]); raise SystemExit
import pandas as pd
tests={
 'SPY_control':'SPY US Equity',
 'natgas_fut':'NG1 Comdty',
 'crude_fut':'CL1 Comdty',
 # US power hub candidates (day-ahead / spot / futures) - guesses to discover what resolves
 'pjm_wh_dap':'PJM WEST DA PEAK Index',
 'pjm_dap2':'PJMPADAP Index',
 'pjm_rt':'PJMDART Index',
 'ercot_nd':'ERCOTND Index',
 'ercot_hub':'ERCOT NORTH Index',
 'caiso_sp15':'CAISO SP15 Index',
 'caiso_np15':'CAISO NP15 Index',
 'miso_indiana':'MISO INDIANA HUB Index',
 'nordpool_sys':'ENOSYSPR Index',
 'epex_de':'ELECDEB Index',
 'elec_pjm':'ELEC PJM Index',
 'pjm_fut':'PJM1 Comdty',
 'power_pjm_c':'PDPAM1 Comdty',
}
import datetime as dt
end=dt.date.today(); start=end-dt.timedelta(days=120)
for name,tk in tests.items():
    try:
        d=blp.bdh(tk,'PX_LAST',start,end)
        n=0 if d is None else len(d.dropna())
        out['tickers'][name]={'ticker':tk,'rows':int(n),'ok':bool(n>0)}
        if n>0:
            try: out['tickers'][name]['last']=float(d.dropna().iloc[-1,0])
            except: pass
        lg(f"{name} ({tk}): rows={n}")
    except Exception as e:
        out['tickers'][name]={'ticker':tk,'err':str(e)[:120]}; lg(f"{name} ({tk}) ERR {str(e)[:100]}")
out['power_ok']=any(v.get('ok') for k,v in out['tickers'].items() if k not in ('SPY_control','natgas_fut','crude_fut'))
json.dump(out,open(os.path.join(P,"power_probe.json"),"w"),indent=2,default=str)
lg("POWER_PROBE_DONE ok=%s %.0fs"%(out['power_ok'],time.time()-t0))
