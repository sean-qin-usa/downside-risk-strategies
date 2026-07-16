f="/home/steveqin/gbc_pq/gpu_iqn_mh.py"
lines=open(f).read().split("\n"); out=[]
has_seas=any(l.strip().startswith("SEAS=") for l in lines)
has_newf=any(l.strip().startswith("NEWF=") for l in lines)
for l in lines:
    if l.startswith("FEATS=") :
        if not has_newf:
            out.append('NEWF=["mo_sin","mo_cos","febmar","vrp","ivz","skwz","skew_chg","rv5","rv63","amihud","netcorr","earn_prox"]'); has_newf=True
        if not has_seas:
            out.append('SEAS=["mo_sin","mo_cos","febmar"]'); has_seas=True
        out.append('FEATS=(F9 if FSET=="raw9" else (F17 if FSET=="raw17" else (F9+SEAS if FSET=="seas" else F17+NEWF)))')
        continue
    out.append(l)
open(f,"w").write("\n".join(out))
print("patched. checking defs:")
for l in open(f):
    if l.strip().startswith(("SEAS=","NEWF=","FEATS=")): print("  ",l.strip()[:90])
