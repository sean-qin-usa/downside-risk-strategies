# YOUNG-NAME Phase 2: comparables/characteristic-based fair-value (proxy for the amortized IQN).
# Fair-value physical vol from PEERS (no own-history) -> VRP_peer = IV - peer_vol. Test selection on young cohort
# vs trailing-RV VRP (which failed) and naive. Reuses young_trades.csv (has iv, date, secid, net, age).
import os, glob, math, json, time
import numpy as np, pandas as pd
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
# ---- sector/beta reference (flexible column detection) ----
sector={}; beta={}
for rf in ["eq100_reference.csv","names_reference.csv","panel_mcaps.csv"]:
    f=os.path.join(RAW,rf)
    if not os.path.exists(f): continue
    try:
        d=pd.read_csv(f)
        tcol=[c for c in d.columns if c.lower() in ('ticker','tk','symbol','name')]
        scol=[c for c in d.columns if 'sector' in c.lower() or 'gics' in c.lower() or 'industry' in c.lower()]
        bcol=[c for c in d.columns if c.lower()=='beta' or 'beta' in c.lower()]
        if tcol and scol:
            for r in d.itertuples(index=False):
                tk=str(getattr(r,tcol[0])); sec=getattr(r,scol[0])
                if tk and isinstance(sec,str): sector.setdefault(tk,sec)
        if tcol and bcol:
            for r in d.itertuples(index=False):
                tk=str(getattr(r,tcol[0])); b=getattr(r,bcol[0])
                try: beta.setdefault(tk,float(b))
                except: pass
    except Exception as e: lg(f"ref {rf} ERR {str(e)[:80]}")
lg("sector coverage=%d beta coverage=%d"%(len(sector),len(beta)))
# ---- per-name trailing RV series + age ----
rvser={}; ageser={}; tk_of={}
for s,tk in sym.items():
    f=os.path.join(RAW,f"tpx_{tk}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    if len(t)<15: continue
    t['date']=pd.to_datetime(t['date']); ser=t.set_index('date')['value'].sort_index()
    lr=np.log(ser/ser.shift(1)); rvser[s]=(lr.rolling(21,min_periods=10).std()*math.sqrt(252))
    ageser[s]=pd.Series(range(len(ser)),index=ser.index); tk_of[s]=tk
lg("names with RV=%d %.0fs"%(len(rvser),time.time()-t0))
# ---- build a monthly panel of (secid, month-end RV, age, sector) for MATURE names (age>=252) as the peer pool ----
allmonths=pd.period_range("2016-01","2025-12",freq="M")
# precompute month-end RV per name
def rv_asof(s,ts):
    z=rvser[s][:ts].dropna(); return float(z.iloc[-1]) if len(z) else np.nan
def age_asof(s,ts):
    z=ageser[s][:ts].dropna(); return int(z.iloc[-1]) if len(z) else np.nan
# market + sector median RV per month (from mature names only)
mkt_rv={}; sec_rv={}
for m in allmonths:
    ts=m.to_timestamp('M'); vals=[]; bysec={}
    for s in rvser:
        a=age_asof(s,ts)
        if a is None or np.isnan(a) or a<252: continue
        rv=rv_asof(s,ts)
        if not np.isfinite(rv): continue
        vals.append(rv)
        sec=sector.get(tk_of[s])
        if sec: bysec.setdefault(sec,[]).append(rv)
    if vals: mkt_rv[m]=float(np.median(vals))
    for sec,v in bysec.items():
        if len(v)>=3: sec_rv[(m,sec)]=float(np.median(v))
lg("month peer pools built %.0fs"%(time.time()-t0))
# ---- attach peer fair-value to young_trades ----
yt=pd.read_csv(os.path.join(P,"young_trades.csv")); yt['ym']=pd.PeriodIndex(yt['ym'],freq='M'); yt['secid']=yt.secid.astype(int)
def peer_vol(row):
    m=row['ym']; s=row['secid']; sec=sector.get(tk_of.get(s,''))
    if sec is not None and (m,sec) in sec_rv: return sec_rv[(m,sec)]
    return mkt_rv.get(m,np.nan)
yt['peer_vol']=yt.apply(peer_vol,axis=1); yt['vrp_peer']=yt['iv']-yt['peer_vol']
yt.to_csv(os.path.join(P,"young_phase2_trades.csv"),index=False)
def sr(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
def stats(sub,col):
    if not len(sub): return dict(SR=None,avg_bp=None,worst_mo=None,n=0)
    m=sub.groupby('ym')[col].mean(); return dict(SR=sr(m),avg_bp=round(float(sub[col].mean()*1e4),1),worst_mo=round(float(m.min()*100),2),n=int(len(sub)))
out={'sector_cov':len(sector),'note':'peer_vol=sector(or market) median trailing-RV of MATURE names, NO own-history. vrp_peer=IV-peer_vol.'}
for lbl,lo,hi in [('young1_<=252',0,252),('young2_253-504',253,504),('mid_505-1512',505,1512)]:
    c=yt[(yt.age>=lo)&(yt.age<=hi)].dropna(subset=['vrp_peer'])
    if not len(c): continue
    def topq(frame,col): return frame.groupby('ym',group_keys=False).apply(lambda g:g[g[col]>=g[col].quantile(0.75)])
    cell={'n':int(len(c)),
      'NAIVE_mid':stats(c,'net_mid'),'NAIVE_bid':stats(c,'net_bid'),
      'VRPtrail_mid':stats(topq(c.dropna(subset=['vrp']),'vrp'),'net_mid'),
      'VRPtrail_bid':stats(topq(c.dropna(subset=['vrp']),'vrp'),'net_bid'),
      'VRPpeer_mid':stats(topq(c,'vrp_peer'),'net_mid'),
      'VRPpeer_bid':stats(topq(c,'vrp_peer'),'net_bid'),
      'corr_peer_vs_trail_vrp':round(float(c[['vrp','vrp_peer']].corr().iloc[0,1]),2) if c['vrp'].notna().sum()>10 else None}
    out[lbl]=cell
    lg(f"{lbl}: naive_mid {cell['NAIVE_mid']['SR']} | VRPtrail_mid {cell['VRPtrail_mid']['SR']} | VRPpeer_mid {cell['VRPpeer_mid']['SR']} || bid: naive {cell['NAIVE_bid']['SR']} peer {cell['VRPpeer_bid']['SR']}")
json.dump(out,open(os.path.join(P,"young_phase2_results.json"),"w"),indent=2,default=str)
lg("PHASE2\n"+json.dumps(out,indent=2,default=str)); lg("JOBP2DONE %.0fs"%(time.time()-t0))
