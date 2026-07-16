# RIGOR GAP 2 (weekly Q-side VRP) + EARNINGS-VRP robustness. Local, reuses established leakage-free method.
import os, glob, time, math, json
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
oi=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False)
ranked=[int(s) for s in oi.index]; oi_rank={s:i for i,s in enumerate(ranked)}
# ---- load px + trailing RV per name ----
px={}; rv={}
for s in ranked:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    if len(t)<40: continue
    t['date']=pd.to_datetime(t['date']); ser=t.set_index('date')['value'].sort_index()
    px[s]=ser; lr=np.log(ser/ser.shift(1)); rv[s]=(lr.rolling(21).std()*math.sqrt(252))
uset=set(px); lg("names px=%d %.0fs"%(len(uset),time.time()-t0))
def pxat(s,dt):
    z=px[s][:dt]; return float(z.iloc[-1]) if len(z) else np.nan
def rvat(s,dt):
    z=rv[s][:dt].dropna(); return float(z.iloc[-1]) if len(z) else np.nan
def sr(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None

def build(glob_pat, dlo, dhi):
    rows=[]
    for f in sorted(glob.glob(os.path.join(W,glob_pat))):
        yr=int(os.path.basename(f).split('_')[-1][:4])
        if yr<2016: continue
        parts=[]
        for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
            parts.append(ch[ch.secid.isin(uset)])
        d=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
        if not len(d): continue
        d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
        d=d[(d.dte>=dlo)&(d.dte<=dhi)&(d.best_bid>0)&(d.best_offer>0)&(d.impl_volatility>0)&(d.delta<0)]
        d['cyc']=d['date'].dt.to_period('W')
        for (s,c),g in d.groupby(['secid','cyc']):
            g=g[g.date==g.date.min()]
            if not len(g): continue
            r=g.iloc[(g.delta+0.12).abs().values.argmin()]
            K=r.strike_price/1000.0; sig=float(r.impl_volatility); T=r.dte/365.0; dl=float(r.delta)
            if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
            d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
            p0=pxat(s,r.date); p1=pxat(s,r.exdate); rvt=rvat(s,r.date)
            if not(np.isfinite(p0) and np.isfinite(p1) and p0>0 and np.isfinite(rvt)): continue
            Sx=Se*(p1/p0); mid=(float(r.best_bid)+float(r.best_offer))/2; net=(mid-max(K-Sx,0.0))/K
            rows.append((s,r.date,net,sig,rvt))
        lg("  %s %d %d %.0fs"%(glob_pat,yr,len(rows),time.time()-t0))
    df=pd.DataFrame(rows,columns=['secid','date','net','iv','rv_trail'])
    df['ym']=df['date'].dt.to_period('M'); df['vrp']=df['iv']-df['rv_trail']; df['rank']=df.secid.map(oi_rank)
    return df

def vrp_select(df, topn=100):
    d=df[df['rank']<topn].dropna(subset=['vrp'])
    out={}
    for lbl,q in [('all',None),('top50pct',0.5),('top25pct',0.75),('top10pct',0.90)]:
        if q is None: keep=d
        else: keep=d.groupby('ym',group_keys=False).apply(lambda g:g[g.vrp>=g.vrp.quantile(q)])
        m=keep.groupby('ym')['net'].mean()
        out[lbl]=dict(SR=sr(m), avg_bp=round(float(keep.net.mean()*1e4),1), n=int(len(keep)), worst_mo=round(float(m.min()*100),2))
    return out

RES={}
# ===== WEEKLY (rigor gap 2) =====
try:
    wk=build('spreads_dte05_15_*.csv.gz',5,15); wk.to_csv(os.path.join(P,"weekly_trades.csv"),index=False)
    RES['WEEKLY']=dict(n_trades=len(wk), n_names=int(wk.secid.nunique()), vrp_select=vrp_select(wk))
    lg("WEEKLY done %.0fs"%(time.time()-t0))
except Exception as e:
    RES['WEEKLY']={'ERR':str(e)[:200]}; lg("WEEKLY ERR "+str(e)[:200])
# monthly comparison (reuse existing improve_trades.csv)
try:
    mo=pd.read_csv(os.path.join(P,"improve_trades.csv")); mo['ym']=pd.PeriodIndex(mo['ym'],freq='M'); mo['rank']=mo.secid.astype(int).map(oi_rank)
    RES['MONTHLY_ref']=dict(n_trades=len(mo), vrp_select=vrp_select(mo))
except Exception as e:
    RES['MONTHLY_ref']={'ERR':str(e)[:200]}
json.dump(RES,open(os.path.join(P,"weekly_qside_results.json"),"w"),indent=2,default=str)
lg("WEEKLY_RESULTS\n"+json.dumps(RES,indent=2,default=str))

# ===== EARNINGS-VRP robustness (task 4) =====
try:
    ed=pd.read_csv(os.path.join(RAW,"earnings_dates.csv")); ed['ann_date']=pd.to_datetime(ed['ann_date'],errors='coerce')
    ed=ed.dropna(subset=['ann_date'])
    ann_by_tk={tk:np.sort(g['ann_date'].values) for tk,g in ed.groupby('ticker')}
    mo=pd.read_csv(os.path.join(P,"improve_trades.csv")); mo['date']=pd.to_datetime(mo['date']); mo['ym']=pd.PeriodIndex(mo['ym'],freq='M')
    mo['rank']=mo.secid.astype(int).map(oi_rank); mo['tk']=mo.secid.astype(int).map(sym)
    # window = entry .. entry+35d (monthly option life)
    def spans_earn(row):
        a=ann_by_tk.get(row['tk'])
        if a is None or not len(a): return False
        lo=np.datetime64(row['date']); hi=lo+np.timedelta64(35,'D')
        return bool(((a>=lo)&(a<=hi)).any())
    mo['earn']=mo.apply(spans_earn,axis=1)
    d=mo[mo['rank']<100].dropna(subset=['vrp'])
    top=d.groupby('ym',group_keys=False).apply(lambda g:g[g.vrp>=g.vrp.quantile(0.90)])
    def bookSR(frame):
        m=frame.groupby('ym')['net'].mean(); return sr(m), round(float(frame.net.mean()*1e4),1), int(len(frame))
    E={}
    E['pct_all_trades_earn']=round(float(d['earn'].mean()*100),1)
    E['pct_selected_earn']=round(float(top['earn'].mean()*100),1)
    E['avg_vrp_earn']=round(float(d[d.earn].vrp.mean()),3); E['avg_vrp_noearn']=round(float(d[~d.earn].vrp.mean()),3)
    E['avg_iv_earn']=round(float(d[d.earn].iv.mean()),3); E['avg_iv_noearn']=round(float(d[~d.earn].iv.mean()),3)
    for lbl,fr in [('top10_ALL',top),('top10_earn_only',top[top.earn]),('top10_NO_earn',top[~top.earn])]:
        s,bp,n=bookSR(fr); E[lbl]=dict(SR=s,avg_bp=bp,n=n)
    # SIZE-DOWN-EARNINGS variant: weight earnings trades 0.5x within each month's selected book
    def sizedown(g):
        g=g.copy(); g['w']=np.where(g['earn'],0.5,1.0); g['w']/=g['w'].sum(); return (g['net']*g['w']).sum()
    m_base=top.groupby('ym')['net'].mean(); m_sd=top.groupby('ym').apply(sizedown)
    E['book_equalwt_SR']=sr(m_base); E['book_earnHALF_SR']=sr(m_sd)
    E['book_earnHALF_ann_bp']=round(float(m_sd.mean()*1e4),1); E['book_equal_ann_bp']=round(float(m_base.mean()*1e4),1)
    RES_E=E
    json.dump(E,open(os.path.join(P,"earnings_deep_results.json"),"w"),indent=2,default=str)
    lg("EARNINGS_RESULTS\n"+json.dumps(E,indent=2,default=str))
except Exception as e:
    import traceback; lg("EARN ERR "+traceback.format_exc()[:400])
lg("JOB1DONE %.0fs"%(time.time()-t0))
