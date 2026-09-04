# Calls re-pull (+ ATM-put band) to enable risk-reversal / straddle / strangle structure tests.
# Mirrors wrds_pull_run2.py auth exactly. Uses your saved pgpass; NEVER handles the password.
# Reuses the existing secids.csv (no ticker-file needed). Resumable: skips files already pulled.
import builtins, os
def _fake_input(prompt=''):
    s=str(prompt).lower()
    if 'username' in s: return 'seanqin2028'
    if 'y/n' in s or 'create' in s: return 'n'
    return 'n'
builtins.input = _fake_input
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'
os.environ.setdefault('PGUSER','seanqin2028')

import pandas as pd, wrds
OUT=r"C:\GBC_data\data\wrds"
os.makedirs(OUT, exist_ok=True)
print("connecting...", flush=True)
db = wrds.Connection(wrds_username='seanqin2028')
print("CONNECTED OK", flush=True)

# reuse the secids already pulled
sec=pd.read_csv(os.path.join(OUT,'secids.csv'))
secl=",".join(str(int(s)) for s in sec.secid.dropna().unique())
print("secids:", sec.secid.nunique(), flush=True)

YEARS=range(2005,2027)   # matches the puts pull range; edit if you only want 2016+

# 1) CALLS: cp_flag='C', OTM through ATM (delta 0.03..0.55) -> enables risk reversal + call legs
for yr in YEARS:
    f=os.path.join(OUT,f'calls_{yr}.csv.gz')
    if os.path.exists(f): print('calls',yr,'skip',flush=True); continue
    try:
        q=f"""select o.secid,o.date,o.exdate,o.cp_flag,o.strike_price,o.best_bid,
              o.best_offer,o.impl_volatility,o.volume,o.open_interest,o.delta
              from optionm.opprcd{yr} o
              where o.secid in ({secl}) and o.cp_flag='C'
                and o.exdate - o.date between 20 and 40
                and o.delta between 0.03 and 0.55"""
        d=db.raw_sql(q); d.to_csv(f,index=False,compression='gzip')
        print('calls',yr,len(d),flush=True)
    except Exception as e:
        print('calls',yr,'ERR',str(e)[:150],flush=True)

# 2) ATM-PUT band: cp_flag='P', delta -0.60..-0.40 (existing puts stop at -0.45) -> completes straddle/butterfly put side
for yr in YEARS:
    f=os.path.join(OUT,f'atmputs_{yr}.csv.gz')
    if os.path.exists(f): print('atmputs',yr,'skip',flush=True); continue
    try:
        q=f"""select o.secid,o.date,o.exdate,o.cp_flag,o.strike_price,o.best_bid,
              o.best_offer,o.impl_volatility,o.volume,o.open_interest,o.delta
              from optionm.opprcd{yr} o
              where o.secid in ({secl}) and o.cp_flag='P'
                and o.exdate - o.date between 20 and 40
                and o.delta between -0.60 and -0.40"""
        d=db.raw_sql(q); d.to_csv(f,index=False,compression='gzip')
        print('atmputs',yr,len(d),flush=True)
    except Exception as e:
        print('atmputs',yr,'ERR',str(e)[:150],flush=True)

db.close()
print('CALLS PULL DONE',flush=True)
