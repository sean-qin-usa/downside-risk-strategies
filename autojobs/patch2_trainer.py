f="/home/steveqin/gbc_pq/gpu_iqn_mh.py"
src=open(f).read()
marker="SEAS=["
if marker not in src:
    # find the FEATS assignment (already patched to include NEWF/camp) and extend with a seas branch
    import re
    # define SEAS right after F17 def
    src=src.replace('F17=F9+["v9r","ty10","curve","hyoas","igoas","mkt63","dd252","d200"]',
                    'F17=F9+["v9r","ty10","curve","hyoas","igoas","mkt63","dd252","d200"]\nSEAS=["mo_sin","mo_cos","febmar"]')
    # replace the FEATS selection line(s) with a version supporting 'seas'
    import re
    src=re.sub(r'FEATS=\(?F9 if FSET=="raw9" else.*',
               'FEATS=(F9 if FSET=="raw9" else (F17 if FSET=="raw17" else (F9+SEAS if FSET=="seas" else F17+NEWF)))',
               src, count=1)
    open(f,"w").write(src); print("PATCH2 ok")
else: print("ALREADY")
# sanity: print the resulting FEATS line
for ln in open(f):
    if ln.strip().startswith("FEATS="): print("LINE:",ln.strip())
