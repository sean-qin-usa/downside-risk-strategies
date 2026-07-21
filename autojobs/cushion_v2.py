import os, json, numpy as np, pandas as pd
RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
bt=pd.read_csv(os.path.join(P,"exp_bt_series.csv"),parse_dates=['date']); bt['ym']=bt.date.dt.to_period('M')
bt=bt[bt.date.dt.year>=2016].sort_values('date'); s=bt.set_index('ym')['s0']/100.0
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
vix=volser('VIX'); vix3m=volser('VIX3M') if volser('VIX3M') is not None else None
vm=vix.resample('ME').last(); vm.index=vm.index.to_period('M'); vm=vm.reindex(s.index).ffill()
vprev=vm.shift(1); vpct=vm.rolling(24,min_periods=6).rank(pct=True)
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
def mdd(x): w=(1+x).cumprod(); return round(float((w/w.cummax()-1).min())*100,1)
def rep(name,size):
    net=s*size
    return dict(rule=name, SR=sr(net), ann_pct=round(float(net.mean()*12*100),2), maxDD=mdd(net),
                worst_pct=round(float(net.min()*100),2), pct_in_mkt=round(float((size>0).mean()*100),0),
                mar2020=round(float((s*size).get(pd.Period('2020-03'),np.nan))*100,2))
one=pd.Series(1.0,index=s.index)
prev=s.shift(1)
rules=[]
rules.append(rep("BASELINE full-size", one))
rules.append(rep("skip month AFTER any down month", (prev>=0).astype(float)))
rules.append(rep("skip AFTER month < -1%", (prev>=-0.01).astype(float)))
rules.append(rep("half-size AFTER down month", np.where(prev<0,0.5,1.0)*one))
rules.append(rep("skip when VIX in top 20% (24m)", (vpct<0.8).astype(float)))
rules.append(rep("skip when VIX rose >20% last mo", (vm<=vprev*1.2).astype(float)))
if vix3m is not None:
    v3=vix3m.resample('ME').last(); v3.index=v3.index.to_period('M'); v3=v3.reindex(s.index).ffill()
    rules.append(rep("skip when VIX>VIX3M (backwardation)", (vm<=v3).astype(float)))
    combo=((vpct<0.8)&(vm<=v3)).astype(float); rules.append(rep("COMBO: not-highVIX AND contango", combo))
else:
    rules.append(dict(rule="VIX3M not found — term-structure gate skipped"))
out={'n_months':len(s),'rules':rules}
json.dump(out,open(os.path.join(P,"cushion_v2_results.json"),"w"),indent=2,default=str)
print(json.dumps(out,indent=2,default=str))
