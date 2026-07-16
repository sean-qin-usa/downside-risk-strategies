# CRSP (WRDS) availability probe for the small-cap / IPO transfer test. Confirms coverage + builds target universe stats.
import builtins, os, json, time
def _fi(p=''):
    s=str(p).lower(); return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'; os.environ.setdefault('PGUSER','seanqin2028')
import pandas as pd, wrds
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
out={}
try:
    db=wrds.Connection(wrds_username='seanqin2028'); lg("CONNECTED %ds"%(time.time()-t0))
except Exception as e:
    json.dump({'connect_error':str(e)[:300]},open(os.path.join(P,"crsp_probe.json"),"w"),indent=2); lg("CONNECT FAIL "+str(e)[:200]); raise SystemExit
def q(name,sql):
    try:
        d=db.raw_sql(sql); out[name]=d.to_dict('records') if hasattr(d,'to_dict') else str(d); lg(f"{name} OK ({len(d) if hasattr(d,'__len__') else '?'})")
        return d
    except Exception as e:
        out[name]=f"ERR {str(e)[:200]}"; lg(f"{name} ERR {str(e)[:160]}")
# 1) does CRSP daily stock file respond + how many names recently
q('universe_2024',"select count(distinct permno) as n_permno from crsp.dsf where date between '2024-01-02' and '2024-12-31'")
# 2) size distribution on a recent date (mcap $mm = |prc|*shrout/1000 ; shrout in thousands)
q('size_buckets',"""select case when abs(prc)*shrout/1000 < 500 then 'micro<0.5B'
  when abs(prc)*shrout/1000 < 2000 then 'small0.5-2B'
  when abs(prc)*shrout/1000 < 10000 then 'mid2-10B' else 'large>10B' end as bucket,
  count(*) as n from crsp.dsf where date='2024-12-31' and prc is not null and shrout>0 group by 1 order by 1""")
# 3) recent IPOs / new listings (common stock) with ticker + start date + how much history
q('recent_ipos',"""select permno, ticker, comnam, st_date, end_date from crsp.stocknames
  where st_date >= '2020-01-01' and shrcd in (10,11) order by st_date desc limit 40""")
# 4) confirm returns pullable for a young small-cap example (first recent-IPO permno)
try:
    ipos=out.get('recent_ipos')
    if isinstance(ipos,list) and ipos:
        pn=ipos[0]['permno']
        q('sample_returns',f"select date, ret, prc, shrout from crsp.dsf where permno={int(pn)} order by date limit 5")
except Exception as e: out['sample_returns']=f"ERR {str(e)[:120]}"
db.close()
json.dump(out,open(os.path.join(P,"crsp_probe.json"),"w"),indent=2,default=str)
lg("CRSP_PROBE_DONE %.0fs"%(time.time()-t0))
