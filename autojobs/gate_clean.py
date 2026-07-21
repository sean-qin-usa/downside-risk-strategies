# DEFINITIVE look-ahead check: gate on PRIOR month-end VIX (known at entry) vs CONTEMPORANEOUS month-end VIX (look-ahead).
import os, numpy as np, pandas as pd
RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
bt=pd.read_csv(os.path.join(P,"exp_bt_series.csv"),parse_dates=['date']); bt['ym']=bt.date.dt.to_period('M'); s=bt.set_index('ym')['s0']/100.0
v=pd.read_csv(os.path.join(RAW,'vol_indices.csv')); cl={c.lower():c for c in v.columns}
vv=v[v[cl['ticker']].astype(str).str.strip().isin(['VIX','VIX Index'])]
if cl.get('field'): vv=vv[vv[cl['field']].astype(str).str.contains('PX_LAST',case=False,na=False)]
vv=vv[[cl['date'],cl['value']]].dropna(); vv[cl['date']]=pd.to_datetime(vv[cl['date']]); vix=vv.set_index(cl['date'])[cl['value']].astype(float).sort_index()
vm=vix.resample('ME').last(); vm.index=vm.index.to_period('M')
mb=pd.read_csv(os.path.join(P,"monthly_book.csv")); mb['ym']=pd.PeriodIndex(mb['ym'],freq='M'); mbmid=mb.set_index('ym')['mid']
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
def era(x,y0,y1): return x[(x.index.year>=y0)&(x.index.year<=y1)]
vm_contemp=vm.copy()                 # vm[M] = end-of-month-M VIX  (LOOK-AHEAD if used to gate month M)
vm_prior=vm.shift(1)                 # prior month-end = known at entry (CLEAN)
print("Gate = stand down if VIX(ref) > level.  Comparing CLEAN (prior-month-end) vs LOOKAHEAD (same-month-end).")
print(f"\nINDEX LEG        | {'CLEAN pre16/16+/full':>26} | {'LOOKAHEAD pre16/16+/full':>28}")
for lv in [15,18,20,25]:
    r={}
    for tag,ref in [('clean',vm_prior),('look',vm_contemp)]:
        rr=ref.reindex(s.index); size=(rr<lv).astype(float); net=s*size
        r[tag]=(sr(era(net,1995,2015)),sr(era(net,2016,2026)),sr(net))
    print(f"  VIX>{lv:<3}        |  {str(r['clean'][0]):>6} {str(r['clean'][1]):>5} {str(r['clean'][2]):>5}       |   {str(r['look'][0]):>6} {str(r['look'][1]):>5} {str(r['look'][2]):>5}")
print("  baseline       |  %5s %5s %5s       |"%(sr(era(s,1995,2015)),sr(era(s,2016,2026)),sr(s)))
print(f"\nSINGLE-NAME MID  | CLEAN SR (2016+) | LOOKAHEAD SR (2016+) | in-mkt%")
for lv in [15,18,20,25]:
    cl_=(vm_prior.reindex(mbmid.index)<lv).astype(float); lk_=(vm_contemp.reindex(mbmid.index)<lv).astype(float)
    print(f"  VIX>{lv:<3}        |     {str(sr(mbmid*cl_)):>6}      |      {str(sr(mbmid*lk_)):>6}       |  {(cl_>0).mean()*100:.0f}")
print("  baseline       |     %6s      |"%sr(mbmid))
print("GATECLEANDONE")
