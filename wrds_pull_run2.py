# Robust WRDS pull: auto-answer any username prompt, password via pgpass.
import builtins, os, sys
def _fake_input(prompt=''):
    s=str(prompt).lower()
    if 'username' in s: return 'seanqin2028'
    if 'y/n' in s or 'create' in s: return 'n'
    return 'n'
builtins.input = _fake_input
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'
os.environ.setdefault('PGUSER','seanqin2028')

import pandas as pd
import wrds
OUT=r"C:\GBC_data\data\wrds"
os.makedirs(OUT, exist_ok=True)
print("connecting...", flush=True)
db = wrds.Connection(wrds_username='seanqin2028')
print("CONNECTED OK", flush=True)

TKFILE=r"C:\GBC_data\code\wrds_tickers.txt"
tks=[l.strip() for l in open(TKFILE)] if os.path.exists(TKFILE) else []
print("tickers:",len(tks), flush=True)
tkl=",".join(f"'{t}'" for t in tks)
sec=db.raw_sql(f"select secid, ticker, cusip from optionm.securd where ticker in ({tkl})")
sec.to_csv(os.path.join(OUT,'secids.csv'), index=False)
print("secids:",len(sec), flush=True)
secl=",".join(str(int(s)) for s in sec.secid.unique())

for yr in range(2005,2027):
    f1=os.path.join(OUT,f'spreads_{yr}.csv.gz')
    if os.path.exists(f1): 
        print(yr,'skip',flush=True); continue
    try:
        q=f"""select o.secid,o.date,o.exdate,o.cp_flag,o.strike_price,o.best_bid,
              o.best_offer,o.impl_volatility,o.volume,o.open_interest,o.delta
              from optionm.opprcd{yr} o
              where o.secid in ({secl}) and o.cp_flag='P'
                and o.exdate - o.date between 20 and 40
                and o.delta between -0.45 and -0.03"""
        d=db.raw_sql(q); d.to_csv(f1,index=False,compression='gzip')
        print('spreads',yr,len(d),flush=True)
    except Exception as e:
        print('spreads',yr,'ERR',str(e)[:150],flush=True)
try:
    d=db.raw_sql("""select permno,dlstdt,dlstcd,dlret,dlretx from crsp.dsedelist
                    where dlstdt>='1996-01-01'""")
    d.to_csv(os.path.join(OUT,'delist_returns.csv.gz'),index=False,compression='gzip')
    print('delist',len(d),flush=True)
except Exception as e:
    print('delist ERR',str(e)[:150],flush=True)
for yr in range(2011,2027):
    f3=os.path.join(OUT,f'surf10d_{yr}.csv.gz')
    if os.path.exists(f3): 
        print('surf',yr,'skip',flush=True); continue
    try:
        d=db.raw_sql(f"""select secid,date,days,delta,impl_volatility
                         from optionm.stdopd{yr}
                         where secid in ({secl}) and days in (10,30) and cp_flag='P'""")
        d.to_csv(f3,index=False,compression='gzip'); print('surf',yr,len(d),flush=True)
    except Exception as e:
        print('surf',yr,'ERR',str(e)[:150],flush=True)
db.close()
print('WRDS PULLS DONE',flush=True)
