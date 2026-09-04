# WRDS pull for the 2008 GFC stress-window robustness test.
# RUN THIS WHERE YOU ARE SIGNED IN TO WRDS (your machine / the host that has wrds credentials in ~/.pgpass).
#   pip install wrds   (if needed)
#   python wrds_pull_2008.py
# Produces crsp_2000_2024_returns.csv (permno,date,ret) for CRSP common shares (shrcd 10/11), 2000-2024, names with
# enough history to span 2008. Pulls year-by-year to stay memory-friendly. Then the calm-vs-stress split + GARCH-t-vs-
# nonparametric tournament runs on it (I'll process it once it lands in the GBC Project folder).
import os, time, pandas as pd
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"crsp_2000_2024_returns.csv")
MIN_OBS=int(os.environ.get("MIN_OBS","3000"))   # ~12yr of trading days; keeps names spanning 2008
import wrds
db=wrds.Connection()   # uses your signed-in credentials
frames=[]
for yr in range(2000,2025):
    q=f"""
      select a.permno, a.date, a.ret
      from crsp.dsf a
      inner join crsp.msenames b
        on a.permno=b.permno and b.namedt<=a.date and a.date<=b.nameendt
      where a.date between '{yr}-01-01' and '{yr}-12-31'
        and b.shrcd in (10,11)
        and a.ret is not null and abs(a.prc) > 5
    """
    df=db.raw_sql(q, date_cols=['date'])
    frames.append(df); print(yr, len(df), "rows", flush=True)
db.close()
alldf=pd.concat(frames, ignore_index=True)
cnt=alldf.groupby('permno')['ret'].transform('count')
alldf=alldf[cnt>=MIN_OBS].sort_values(['permno','date'])
alldf.to_csv(OUT, index=False)
print("SAVED", OUT, "->", alldf['permno'].nunique(), "names,", len(alldf), "rows")
