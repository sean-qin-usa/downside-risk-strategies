# EARNINGS SPLIT: is the VRP edge concentrated in earnings-spanning trades? Pull IBES announce dates via CUSIP.
import builtins, os, numpy as np, pandas as pd
def _fi(p=''):
    s=str(p).lower(); return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'; os.environ.setdefault('PGUSER','seanqin2028')
import wrds, json
W=r"C:\GBC_data\data\wrds"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
imp=pd.read_csv(os.path.join(P,"improve_trades.csv")); imp['date']=pd.to_datetime(imp['date'])
sec=pd.read_csv(os.path.join(W,"secids.csv"))
imp=imp.merge(sec[['secid','cusip']].dropna(),on='secid',how='left') if 'cusip' in sec.columns else imp
db=wrds.Connection(wrds_username='seanqin2028'); print("CONNECTED",flush=True)
cusips=[str(c)[:8] for c in imp['cusip'].dropna().unique()] if 'cusip' in imp.columns else []
ann=pd.DataFrame()
if cusips:
    cl=",".join("'%s'"%c for c in cusips[:600])
    try:
        ann=db.raw_sql(f"select cusip,anndats from ibes.actu_epsus where cusip in ({cl}) and anndats>='2016-01-01' and pdicity='QTR'")
    except Exception as e:
        print("ibes ERR",str(e)[:120],flush=True)
db.close()
if not len(ann): print("no earnings data pulled"); json.dump({"error":"no earnings"},open(os.path.join(P,"earnings_results.json"),"w")); raise SystemExit
ann['anndats']=pd.to_datetime(ann['anndats']); ann['c8']=ann['cusip'].str[:8]
byc={c:g['anndats'].values for c,g in ann.groupby('c8')}
imp['exdate']=pd.to_datetime(imp['exdate']) if 'exdate' in imp.columns else imp['date']+pd.Timedelta(days=30)
imp['c8']=imp['cusip'].astype(str).str[:8]
def spans(r):
    a=byc.get(r['c8'])
    if a is None: return False
    return bool(((a>=np.datetime64(r['date']))&(a<=np.datetime64(r['exdate']))).any())
imp['earn']=imp.apply(spans,axis=1); imp['ym']=pd.PeriodIndex(imp['date'].dt.to_period('M'),freq='M'); imp=imp.dropna(subset=['vrp'])
def SR(x): x=x.dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
def sel(d): thr=d.groupby('ym')['vrp'].transform(lambda s:s.quantile(0.90)); return SR(d[d.vrp>=thr].groupby('ym')['net'].mean())
out=dict(pct_trades_spanning_earnings=round(float(imp['earn'].mean()*100),0),
  top10VRP_ALL=sel(imp), top10VRP_earnings_only=sel(imp[imp.earn]), top10VRP_NO_earnings=sel(imp[~imp.earn]),
  avg_vrp_earn=round(float(imp[imp.earn].vrp.mean()),3), avg_vrp_noearn=round(float(imp[~imp.earn].vrp.mean()),3),
  pct_of_selected_that_are_earnings=None)
# of the top-10% VRP selected, what fraction span earnings?
thr=imp.groupby('ym')['vrp'].transform(lambda s:s.quantile(0.90)); s=imp[imp.vrp>=thr]
out['pct_of_selected_spanning_earnings']=round(float(s['earn'].mean()*100),0)
json.dump(out,open(os.path.join(P,"earnings_results.json"),"w"),indent=2,default=str); print(json.dumps(out,indent=2,default=str)); print("EARNDONE")
