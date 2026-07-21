# Full SPX option chain (all strikes, calls+puts, OI>0, near-dated) + SPX spot -> for dealer GEX.
import builtins, os, math, time
def _fi(p=''): return 'seanqin2028' if 'username' in str(p).lower() else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'; os.environ.setdefault('PGUSER','seanqin2028')
import pandas as pd, wrds
OUT=r"C:\GBC_data\data\wrds"; os.makedirs(OUT,exist_ok=True)
lg=lambda s:print(s,flush=True); t0=time.time()
db=wrds.Connection(wrds_username='seanqin2028'); lg("CONNECTED %.0fs"%(time.time()-t0))
sx=db.raw_sql("select secid,ticker,issue_type,index_flag from optionm.securd where ticker='SPX'")
lg("SPX securd:\n"+sx.to_string())
spx=int(sx.secid.iloc[0]) if len(sx) else 108105
lg("using SPX secid=%d"%spx)
# spot (secprd is all-years table)
try:
    sp=db.raw_sql(f"select date,close from optionm.secprd where secid={spx} and date>='2016-01-01'")
    sp.to_csv(os.path.join(OUT,"spx_spot.csv"),index=False); lg("spot rows %d"%len(sp))
except Exception as e: lg("spot err "+str(e)[:150])
for yr in range(2016,2026):
    f=os.path.join(OUT,f"spx_chain_{yr}.csv.gz")
    if os.path.exists(f): lg("%d skip"%yr); continue
    try:
        d=db.raw_sql(f"""select secid,date,exdate,cp_flag,strike_price,impl_volatility,delta,gamma,open_interest,volume
            from optionm.opprcd{yr}
            where secid={spx} and open_interest>0 and exdate-date between 1 and 45""")
        d.to_csv(f,index=False,compression='gzip'); lg("%d rows=%d %.0fs"%(yr,len(d),time.time()-t0))
    except Exception as e: lg("%d ERR %s"%(yr,str(e)[:150]))
db.close(); lg("GEX PULL DONE")
