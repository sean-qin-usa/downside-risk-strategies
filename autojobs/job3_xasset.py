# CROSS-ASSET ETF: strict IS/OOS split + combined risk-weighted equity curve. Live WRDS.
import builtins, os, math, time, json
def _fi(p=''):
    s=str(p).lower(); return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'; os.environ.setdefault('PGUSER','seanqin2028')
import numpy as np, pandas as pd, wrds
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
ASSETS={'SPY':'equity','QQQ':'equity','IWM':'equity','TLT':'rates','IEF':'rates','GLD':'gold','SLV':'silver',
        'USO':'energy','UNG':'natgas','FXE':'fx_eur','UUP':'fx_usd','HYG':'credit','EEM':'em_equity'}
db=wrds.Connection(wrds_username='seanqin2028'); lg("CONNECTED %ds"%(time.time()-t0))
sec=db.raw_sql("select secid,ticker from optionm.securd where ticker in (%s)"%",".join("'%s'"%t for t in ASSETS))
tk2sec={r.ticker:int(r.secid) for r in sec.itertuples()}
def sleeve(tk):
    sid=tk2sec.get(tk)
    if sid is None: return None
    rows=[]
    for yr in range(2016,2026):
        try:
            o=db.raw_sql(f"""select date,exdate,strike_price,best_bid,best_offer,delta from optionm.opprcd{yr}
                where secid={sid} and cp_flag='P' and exdate-date between 20 and 40 and delta between -0.20 and -0.05 and best_bid>0""")
            sp=db.raw_sql(f"select date,close from optionm.secprd{yr} where secid={sid}")
        except Exception as e:
            lg(f"{tk} {yr} ERR {str(e)[:80]}"); continue
        if not len(o) or not len(sp): continue
        o['date']=pd.to_datetime(o.date); o['exdate']=pd.to_datetime(o.exdate); sp['date']=pd.to_datetime(sp.date)
        spx=sp.set_index('date')['close'].sort_index(); o['cyc']=o['date'].dt.to_period('M')
        for c,g in o.groupby('cyc'):
            g=g[g.date==g.date.min()]
            if not len(g): continue
            r=g.iloc[(g.delta+0.12).abs().values.argmin()]; K=r.strike_price/1000.0; mid=(r.best_bid+r.best_offer)/2
            se=spx[:r.exdate]
            if not len(se): continue
            Sx=float(se.iloc[-1]); rows.append((r.date,(mid-max(K-Sx,0.0))/K))
    if not rows: return None
    d=pd.DataFrame(rows,columns=['date','net']); d['ym']=d['date'].dt.to_period('M'); return d.groupby('ym')['net'].mean()
series={}
for tk in ASSETS:
    s=sleeve(tk)
    if s is not None and len(s)>12: series[tk]=s; lg(f"  {tk} n={len(s)} SR={s.mean()/s.std()*np.sqrt(12):.2f} %.0fs"%(time.time()-t0))
db.close()
M=pd.DataFrame(series); M.to_csv(os.path.join(P,"xasset_monthly.csv"))
def SR(s): s=pd.Series(s).dropna(); return round(float(s.mean()/s.std()*np.sqrt(12)),2) if len(s)>6 and s.std()>0 else None
cls={a:ASSETS[a] for a in M.columns}
def combo_curve(frame):
    Mn=frame.apply(lambda c:c/c.std()); byc=pd.DataFrame({k:Mn[[c for c in frame.columns if cls[c]==k]].mean(axis=1) for k in set(cls[c] for c in frame.columns)})
    return byc.mean(axis=1)
yr=M.index.year
IS=M[yr<=2020]; OOS=M[yr>=2021]
out=dict(
  per_sleeve_SR_full={t:SR(M[t]) for t in M.columns},
  per_sleeve_SR_IS_16_20={t:SR(IS[t]) for t in M.columns},
  per_sleeve_SR_OOS_21_25={t:SR(OOS[t]) for t in M.columns},
  avg_pairwise_corr=round(float(M.corr().where(~np.eye(len(M.columns),dtype=bool)).stack().mean()),2),
  combined_SR_full=SR(combo_curve(M)),
  combined_SR_IS_16_20=SR(combo_curve(IS)) if len(IS)>6 else None,
  combined_SR_OOS_21_25=SR(combo_curve(OOS)) if len(OOS)>6 else None,
  n_sleeves=len(M.columns), n_months=len(M))
# combined equity curve (compounded at 10% target vol on the combined risk-weighted stream)
cc=combo_curve(M).dropna(); scale=0.10/np.sqrt(12)/cc.std() if cc.std()>0 else 1.0
eq=(1+cc*scale).cumprod()
pd.DataFrame({'ym':eq.index.astype(str),'combined_ret':cc.values,'equity':eq.values}).to_csv(os.path.join(P,"xasset_combined_curve.csv"),index=False)
out['combined_CAGR_10voltgt_pct']=round(float((eq.iloc[-1]**(12/len(eq))-1)*100),2)
out['combined_maxDD_pct']=round(float(((eq/eq.cummax())-1).min()*100),2)
json.dump(out,open(os.path.join(P,"xasset_oos_results.json"),"w"),indent=2,default=str)
lg("XASSET_OOS\n"+json.dumps(out,indent=2,default=str)); lg("JOB3DONE %.0fs"%(time.time()-t0))
