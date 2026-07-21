import os, json, numpy as np, pandas as pd
RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
bt=pd.read_csv(os.path.join(P,"exp_bt_series.csv"),parse_dates=['date']); bt['ym']=bt.date.dt.to_period('M'); bt=bt.sort_values('date')
def volser(t):
    for fn in ['vol_indices.csv','bbg_impvol.csv']:
        p=os.path.join(RAW,fn)
        if not os.path.exists(p): continue
        v=pd.read_csv(p); cl={c.lower():c for c in v.columns}; tc,dc,fc,vc=cl.get('ticker'),cl.get('date'),cl.get('field'),cl.get('value')
        if not(tc and dc and vc): continue
        m=v[v[tc].astype(str).str.strip().isin([t,t+' Index',t+' INDEX'])]
        if fc: m=m[m[fc].astype(str).str.contains('PX_LAST',case=False,na=False)]
        if len(m): m=m[[dc,vc]].dropna(); m[dc]=pd.to_datetime(m[dc]); return m.set_index(dc)[vc].astype(float).sort_index()
    return None
vix=volser('VIX')
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
def stats(x): 
    w=(1+x).cumprod(); return dict(SR=sr(x),ann=round(float(x.mean()*12*100),2),maxDD=round(float((w/w.cummax()-1).min())*100,1),worst=round(float(x.min()*100),2),inmkt=round(float((x!=0).mean()*100),0))
out={}
for lab,y0 in [("full 1995-2026",1995),("2005-2026",2005),("2016-2026",2016),("pre-2016 (OOS) 1995-2015",1995)]:
    d=bt[bt.date.dt.year>=y0].copy()
    if lab.startswith("pre"): d=bt[(bt.date.dt.year>=1995)&(bt.date.dt.year<2016)].copy()
    s=d.set_index('ym')['s0']/100.0
    vm=vix.resample('ME').last(); vm.index=vm.index.to_period('M'); vm=vm.reindex(s.index).ffill()
    row={"baseline":stats(s)}
    for thr in [0.70,0.75,0.80,0.85,0.90]:
        vpct=vm.rolling(24,min_periods=6).rank(pct=True); size=(vpct<thr).astype(float)
        row[f"gate_top{int((1-thr)*100)}pct"]=stats(s*size)
    out[lab]=row
json.dump(out,open(os.path.join(P,"cushion_v3_results.json"),"w"),indent=2,default=str)
print(json.dumps(out,indent=2,default=str))
