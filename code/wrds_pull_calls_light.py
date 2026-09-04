# LIGHT calls pull: top-60 liquid names, 2016-2025 only, narrow delta -> small & fast (won't hang).
import builtins, os
def _fake_input(p=''):
    s=str(p).lower()
    return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fake_input
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'
os.environ.setdefault('PGUSER','seanqin2028')
import pandas as pd, wrds, time
OUT=r"C:\GBC_data\data\wrds"
print("connecting...",flush=True); db=wrds.Connection(wrds_username='seanqin2028'); print("CONNECTED",flush=True)
top=[int(s) for s in pd.read_csv(os.path.join(OUT,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:60]]
secl=",".join(str(s) for s in top); print("top secids",len(top),flush=True)
t0=time.time()
for yr in range(2016,2026):
    f=os.path.join(OUT,f'calls_{yr}.csv.gz')
    if os.path.exists(f): print('calls',yr,'skip',flush=True); continue
    try:
        q=f"""select o.secid,o.date,o.exdate,o.cp_flag,o.strike_price,o.best_bid,o.best_offer,
              o.impl_volatility,o.volume,o.open_interest,o.delta from optionm.opprcd{yr} o
              where o.secid in ({secl}) and o.cp_flag='C'
                and o.exdate-o.date between 20 and 40 and o.delta between 0.05 and 0.55"""
        d=db.raw_sql(q); d.to_csv(f,index=False,compression='gzip'); print('calls',yr,len(d),round(time.time()-t0),flush=True)
    except Exception as e: print('calls',yr,'ERR',str(e)[:120],flush=True)
for yr in range(2016,2026):
    f=os.path.join(OUT,f'atmputs_{yr}.csv.gz')
    if os.path.exists(f): print('atmputs',yr,'skip',flush=True); continue
    try:
        q=f"""select o.secid,o.date,o.exdate,o.cp_flag,o.strike_price,o.best_bid,o.best_offer,
              o.impl_volatility,o.volume,o.open_interest,o.delta from optionm.opprcd{yr} o
              where o.secid in ({secl}) and o.cp_flag='P'
                and o.exdate-o.date between 20 and 40 and o.delta between -0.60 and -0.40"""
        d=db.raw_sql(q); d.to_csv(f,index=False,compression='gzip'); print('atmputs',yr,len(d),round(time.time()-t0),flush=True)
    except Exception as e: print('atmputs',yr,'ERR',str(e)[:120],flush=True)
db.close(); print('LIGHTCALLSDONE',flush=True)
