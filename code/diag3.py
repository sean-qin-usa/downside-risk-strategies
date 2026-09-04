import os, glob, time
base=r"C:\GBC_data"
out=r"C:\Users\OWNER\Claude\Projects\GBC Project\wrds_diag3_out.txt"
L=[]; p=lambda s:L.append(str(s))
p("DIAG3 "+time.ctime())
def show(path,label,head=6000):
    if os.path.exists(path):
        t=open(path,errors='replace').read()
        p("\n===== %s  (%s) =====\n%s"%(label,path,t[:head]))
    else: p("\n%s : MISSING (%s)"%(label,path))
# job bats (from done/)
for f in ["queue\\done\\job_wrds_pulls3.bat","queue\\done\\job_wrds_pulls2.bat.skipped","queue\\done\\job_wrds_pulls.bat","run_queue_watcher.bat","run_snapshot.bat"]:
    show(os.path.join(base,f),f)
# wrds pull python script - targeted dirs only (fast)
hits=[]
for d in [base, os.path.join(base,"code"), os.path.join(base,"code","pq_trade")]:
    hits += glob.glob(os.path.join(d,"*wrds*.py"))
for h in sorted(set(hits)): show(h,"PYSCRIPT "+os.path.basename(h))
# confirm pgpass standard path + folder
appdata=os.environ.get('APPDATA','')
pgd=os.path.join(appdata,"postgresql")
p("\npostgresql folder exists: %s | pgpass.conf exists: %s"%(os.path.isdir(pgd), os.path.exists(os.path.join(pgd,"pgpass.conf"))))
open(out,"w").write("\n".join(L)); print("wrote",out)
