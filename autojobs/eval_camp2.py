import os, json
import numpy as np, pandas as pd
PROJ=r"C:\Users\OWNER\Claude\Projects\GBC Project"; RES=r"C:\GBC_data\results\pq_trade"
c2=os.path.join(PROJ,"mh_quantiles_camp2.csv"); base=os.path.join(RES,"mh_quantiles_gpu_v2.csv")
if not os.path.exists(c2): print("camp2 output not local yet"); raise SystemExit
def bymo(f):
    d=pd.read_csv(f); d=d[d.h==21].copy(); d['date']=pd.to_datetime(d.date); d['mo']=d.date.dt.month; d=d[d.y.notna()]
    return {m:{'05':round(float((s.y<s['p05']).mean()),3),'10':round(float((s.y<s['p10']).mean()),3),'n':int(len(s))} for m,s in [(m,d[d.mo==m]) for m in range(1,13)]}
C=bymo(c2); B=bymo(base)
print("mo  raw9_p05  camp2_p05  | raw9_p10  camp2_p10   (nominal .05 / .10)")
for m in range(1,13):
    print(f"{m:2d}   {B[m]['05']:.3f}     {C[m]['05']:.3f}    |  {B[m]['10']:.3f}    {C[m]['10']:.3f}")
print("\nFEB(2): raw9 p05 %.3f camp2 %.3f | MAR(3): raw9 %.3f camp2 %.3f  (nominal .05)"%(B[2]['05'],C[2]['05'],B[3]['05'],C[3]['05']))
json.dump({'camp2':C,'raw9':B},open(os.path.join(PROJ,"camp2_bymonth.json"),"w"),indent=2)
print("saved")
