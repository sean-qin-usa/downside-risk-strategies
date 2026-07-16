import pandas as pd
d=pd.read_csv(r"C:\Users\OWNER\Claude\Projects\GBC Project\mh_panel_v2.csv.gz")
print("shape",d.shape); print("cols",list(d.columns))
print("n_names",d.tk.nunique()); print("names sample",sorted(d.tk.unique())[:20])
print("date range",d.date.min(),d.date.max())
print("dates per name (median)", d.groupby('tk').size().median())
print("sample dates for AAPL:", list(d[d.tk=='AAPL'].date.head(6)) if (d.tk=='AAPL').any() else "no AAPL")
