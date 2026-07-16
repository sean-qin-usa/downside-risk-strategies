f="/home/steveqin/gbc_pq/gpu_iqn_mh.py"
src=open(f).read()
if "NEWF=" not in src:
    old='FEATS=F9 if FSET=="raw9" else F17'
    new=('NEWF=["mo_sin","mo_cos","febmar","vrp","ivz","skwz","skew_chg","rv5","rv63","amihud","netcorr","earn_prox"]\n'
         'FEATS=(F9 if FSET=="raw9" else (F17 if FSET=="raw17" else F17+NEWF))')
    assert old in src, "FEATS line not found"
    open(f,"w").write(src.replace(old,new)); print("PATCHED ok")
else: print("ALREADY patched")
