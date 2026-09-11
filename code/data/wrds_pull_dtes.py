# Follow-up WRDS pull: short (weekly ~5-15 DTE) and long (~45-70 DTE) put quotes,
# to bracket the monthly 20-40 DTE already pulled. Robust auth (input patch).
import builtins, os
def _fi(prompt=''):
    s=str(prompt).lower()
    return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'
os.environ.setdefault('PGUSER','seanqin2028')
import pandas as pd, wrds
OUT=r"C:\GBC_data\data\wrds"; os.makedirs(OUT,exist_ok=True)
print("connecting...",flush=True)
db=wrds.Connection(wrds_username='seanqin2028'); print("CONNECTED OK",flush=True)
sec=pd.read_csv(os.path.join(OUT,'secids.csv'))
secl=",".join(str(int(s)) for s in sec.secid.dropna().unique())
print("secids:",sec.secid.nunique(),flush=True)
BANDS={'dte05_15':(5,15), 'dte45_70':(45,70)}
for tag,(lo,hi) in BANDS.items():
    for yr in range(2005,2026):
        f=os.path.join(OUT,f'spreads_{tag}_{yr}.csv.gz')
        if os.path.exists(f):
            print(tag,yr,'skip',flush=True); continue
        try:
            q=f"""select o.secid,o.date,o.exdate,o.cp_flag,o.strike_price,o.best_bid,
                  o.best_offer,o.impl_volatility,o.volume,o.open_interest,o.delta
                  from optionm.opprcd{yr} o
                  where o.secid in ({secl}) and o.cp_flag='P'
                    and o.exdate - o.date between {lo} and {hi}
                    and o.delta between -0.45 and -0.03"""
            d=db.raw_sql(q); d.to_csv(f,index=False,compression='gzip')
            print(tag,yr,len(d),flush=True)
        except Exception as e:
            print(tag,yr,'ERR',str(e)[:120],flush=True)
db.close(); print("DTE PULLS DONE",flush=True)
