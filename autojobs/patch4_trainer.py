f="/home/steveqin/gbc_pq/gpu_iqn_mh.py"
lines=open(f).read().split("\n"); out=[]; inserted=False
drop=("NEWF=","SEAS=","FEATS=")
for l in lines:
    s=l.strip()
    if any(s.startswith(p) for p in drop):   # remove ALL old defs (untangle)
        continue
    out.append(l)
    if s.startswith("F17=") and not inserted:
        out.append('NEWF=["mo_sin","mo_cos","febmar","vrp","ivz","skwz","skew_chg","rv5","rv63","amihud","netcorr","earn_prox"]')
        out.append('SEAS=["mo_sin","mo_cos","febmar"]')
        out.append('FEATS=(F9 if FSET=="raw9" else (F17 if FSET=="raw17" else (F9+SEAS if FSET=="seas" else F17+NEWF)))')
        inserted=True
open(f,"w").write("\n".join(out))
import ast; ast.parse(open(f).read())
print("CLEAN PATCH inserted=%s"%inserted)
import subprocess
for ln in open(f):
    if ln.strip().startswith(("F9=","F17=","NEWF=","SEAS=","FEATS=")): print("  ",ln.rstrip()[:80])
