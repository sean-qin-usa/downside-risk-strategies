# Refine ABSOLUTE-VIX gate (the era-stable signal). Index leg (both eras) + single-name mid book.
import os, json, numpy as np, pandas as pd
RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
bt=pd.read_csv(os.path.join(P,"exp_bt_series.csv"),parse_dates=['date']); bt['ym']=bt.date.dt.to_period('M')
s_all=bt.set_index('ym')['s0']/100.0
v=pd.read_csv(os.path.join(RAW,'vol_indices.csv')); cl={c.lower():c for c in v.columns}
vv=v[v[cl['ticker']].astype(str).str.strip().isin(['VIX','VIX Index'])]
if cl.get('field'): vv=vv[vv[cl['field']].astype(str).str.contains('PX_LAST',case=False,na=False)]
vv=vv[[cl['date'],cl['value']]].dropna(); vv[cl['date']]=pd.to_datetime(vv[cl['date']])
vix=vv.set_index(cl['date'])[cl['value']].astype(float).sort_index()
vm=vix.resample('ME').last(); vm.index=vm.index.to_period('M')
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
def era(x,y0,y1): return x[(x.index.year>=y0)&(x.index.year<=y1)]
# single-name mid book (2016+)
mb=None
if os.path.exists(os.path.join(P,"monthly_book.csv")):
    mb=pd.read_csv(os.path.join(P,"monthly_book.csv")); mb['ym']=pd.PeriodIndex(mb['ym'],freq='M'); mb=mb.set_index('ym')['mid']
print("ABS-VIX GATE REFINE (skip month if prior-month-end VIX > level)")
print(f"{'lvl':>4} | idx_pre2016 idx_2016+ idx_full inmkt% | sname_mid_2016+ inmkt%")
vmr=vm.reindex(s_all.index).ffill()
for lv in [15,18,20,22,25,28,30,100]:
    size=(vmr<lv).astype(float); net=s_all*size
    row=f"{lv:>4} | {str(sr(era(net,1995,2015))):>10} {str(sr(era(net,2016,2026))):>9} {str(sr(net)):>8} {(size>0).mean()*100:>5.0f} |"
    if mb is not None:
        vmb=vm.reindex(mb.index).ffill(); sz=(vmb<lv).astype(float); nb=mb*sz
        row+=f" {str(sr(nb)):>14} {(sz>0).mean()*100:>5.0f}"
    print(row)
print("GATEABSDONE")
