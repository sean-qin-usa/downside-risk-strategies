# Robust VIX-gate parameter study: threshold x window x signal-type x ERA. Goal: find era-STABLE params (anti-overfit).
import os, json, numpy as np, pandas as pd
RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
bt=pd.read_csv(os.path.join(P,"exp_bt_series.csv"),parse_dates=['date']); bt['ym']=bt.date.dt.to_period('M')
s_all=bt.set_index('ym')['s0']/100.0
v=pd.read_csv(os.path.join(RAW,'vol_indices.csv')); cl={c.lower():c for c in v.columns}
vv=v[v[cl['ticker']].astype(str).str.strip().isin(['VIX','VIX Index'])]
if cl.get('field'): vv=vv[vv[cl['field']].astype(str).str.contains('PX_LAST',case=False,na=False)]
vv=vv[[cl['date'],cl['value']]].dropna(); vv[cl['date']]=pd.to_datetime(vv[cl['date']])
vix=vv.set_index(cl['date'])[cl['value']].astype(float).sort_index()
vm_all=vix.resample('ME').last(); vm_all.index=vm_all.index.to_period('M')
def sr(x): return float(x.mean()/x.std()*np.sqrt(12)) if len(x)>6 and x.std()>0 else np.nan
def era(x,y0,y1): return x[(x.index.year>=y0)&(x.index.year<=y1)]
rows=[]
# signal 1: VIX level percentile, rolling window W, skip if pct>=thr
for W in [12,18,24,36]:
    for thr in [.70,.75,.80,.85,.90]:
        vpct=vm_all.rolling(W,min_periods=6).rank(pct=True).reindex(s_all.index).ffill()
        size=(vpct<thr).astype(float); net=s_all*size
        rows.append(dict(sig=f"VIXlvl_w{W}_top{int((1-thr)*100)}", full=sr(net), pre2016=sr(era(net,1995,2015)), y2016=sr(era(net,2016,2026)), inmkt=round(float((size>0).mean()*100),0)))
# signal 2: VIX MoM change, skip if rose > X%
for X in [.10,.15,.20,.30]:
    ch=vm_all.pct_change().reindex(s_all.index)
    size=(ch<=X).astype(float); net=s_all*size
    rows.append(dict(sig=f"VIXchg_skip>{int(X*100)}%", full=sr(net), pre2016=sr(era(net,1995,2015)), y2016=sr(era(net,2016,2026)), inmkt=round(float((size>0).mean()*100),0)))
# signal 3: absolute VIX level threshold
for lv in [20,25,30,35]:
    vmr=vm_all.reindex(s_all.index).ffill(); size=(vmr<lv).astype(float); net=s_all*size
    rows.append(dict(sig=f"VIXabs_skip>{lv}", full=sr(net), pre2016=sr(era(net,1995,2015)), y2016=sr(era(net,2016,2026)), inmkt=round(float((size>0).mean()*100),0)))
base=dict(sig="BASELINE_nogate", full=sr(s_all), pre2016=sr(era(s_all,1995,2015)), y2016=sr(era(s_all,2016,2026)), inmkt=100.0)
df=pd.DataFrame([base]+rows)
for c in ['full','pre2016','y2016']: df[c]=df[c].round(2)
# stability: helps in BOTH pre2016 and 2016+ vs baseline
b=df.iloc[0]; df['stable_uplift']=((df.pre2016>b.pre2016)&(df.y2016>b.y2016))
df=df.sort_values('full',ascending=False)
df.to_csv(os.path.join(P,"gate_param_sweep.csv"),index=False)
print("BASELINE pre2016=%.2f  2016+=%.2f  full=%.2f"%(b.pre2016,b.y2016,b.full))
print("\n--- params that help in BOTH eras (stable, anti-overfit) ---")
print(df[df.stable_uplift][['sig','pre2016','y2016','full','inmkt']].to_string(index=False))
print("\n--- top 10 by full-sample SR (may be overfit) ---")
print(df[['sig','pre2016','y2016','full','inmkt','stable_uplift']].head(10).to_string(index=False))
print("GATESWEEPDONE")
