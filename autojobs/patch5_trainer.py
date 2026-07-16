f="/home/steveqin/gbc_pq/gpu_iqn_mh.py"
lines=open(f).read().split("\n"); out=[]; ins=False
drop=("NEWF=","SEAS=","CAMP2=","FEATS=")
for l in lines:
    s=l.strip()
    if any(s.startswith(p) for p in drop): continue
    out.append(l)
    if s.startswith("F17=") and not ins:
        out.append('NEWF=["mo_sin","mo_cos","febmar","vrp","ivz","skwz","skew_chg","rv5","rv63","amihud","netcorr","earn_prox"]')
        out.append('SEAS=["mo_sin","mo_cos","febmar"]')
        out.append('CAMP2=["vrp","ivz","skwz","skew_chg","rv5","rv63","amihud","netcorr","earn_prox"]')
        out.append('FEATS=(F9 if FSET=="raw9" else (F17 if FSET=="raw17" else (F9+SEAS if FSET=="seas" else (F9+CAMP2 if FSET=="camp2" else F17+NEWF))))')
        ins=True
open(f,"w").write("\n".join(out))
import ast; ast.parse(open(f).read()); print("CLEAN5 ins=%s"%ins)
