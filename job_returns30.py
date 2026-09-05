# Pull CRSP daily returns 2014-2024 for the 30 TAQ intraday tickers, matched by ticker via crsp.stocknames
# (common shares, name-range overlapping the window, longest overlap). Writes crsp_returns_30.csv (ticker,date,ret).
import time, sys, datetime as dt
import wrds, numpy as np, pandas as pd
t0=time.time(); lg=lambda s:print(s,flush=True)
db=wrds.Connection(wrds_username='seanqin2028')
NAMES=['AAPL','MSFT','JPM','XOM','JNJ','PG','KO','WMT','CVX','HD','PFE','MRK','CSCO','INTC','VZ',
       'T','BAC','WFC','C','GS','IBM','MMM','CAT','BA','DIS','MCD','NKE','ORCL','QCOM','TXN']
inlist="','".join(NAMES)
sn=db.raw_sql("select permno,namedt,nameenddt,ticker,comnam,shrcd,exchcd from crsp.stocknames where ticker in ('%s')"%inlist)
sn['namedt']=pd.to_datetime(sn['namedt']); sn['nameenddt']=pd.to_datetime(sn['nameenddt'])
W0=pd.Timestamp('2014-01-01'); W1=pd.Timestamp('2024-12-31')
sn=sn[(sn['shrcd'].isin([10,11]))]
sn['ov']=(sn['nameenddt'].clip(upper=W1)-sn['namedt'].clip(lower=W0)).dt.days
sn=sn[sn['ov']>0]
pick={}
for tk,g in sn.groupby('ticker'):
    g=g.sort_values('ov',ascending=False); pick[tk]=int(g.iloc[0]['permno'])
lg('mapped %d/30: %s'%(len(pick),pick))
missing=[t for t in NAMES if t not in pick]; lg('missing: %s'%missing)
perms=list(set(pick.values())); pinlist=",".join(str(p) for p in perms)
df=db.raw_sql("select permno,date,ret from crsp.dsf where permno in (%s) and date between '2014-01-01' and '2024-12-31'"%pinlist)
df['date']=pd.to_datetime(df['date']); df['ret']=pd.to_numeric(df['ret'],errors='coerce')
p2t={p:t for t,p in pick.items()}
df['ticker']=df['permno'].map(p2t)
df=df.dropna(subset=['ret','ticker'])[['ticker','date','ret']].sort_values(['ticker','date'])
df.to_csv('crsp_returns_30.csv',index=False)
lg('rows=%d tickers=%d range=%s..%s %.0fs'%(len(df),df['ticker'].nunique(),df['date'].min().date(),df['date'].max().date(),time.time()-t0))
lg('per-ticker days:'); lg(df.groupby('ticker')['date'].count().to_string())
