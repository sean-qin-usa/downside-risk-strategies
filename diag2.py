import os, glob, time
base=r"C:\GBC_data"
out=r"C:\Users\OWNER\Claude\Projects\GBC Project\wrds_diag2_out.txt"
L=[]
def p(s): L.append(str(s))
p("DIAG2 "+time.ctime())
# find wrds pull script + any pgpass anywhere under user
def show(path,label,tail=0,head=0):
    if os.path.exists(path):
        t=open(path,errors='replace').read()
        if tail: t=t[-tail:]
        if head: t=t[:head]
        p("\n----- %s (%s) -----\n%s"%(label,path,t))
    else: p("\n%s MISSING: %s"%(label,path))
# locate wrds_pulls*.py
for d in [os.path.join(base,"code"),os.path.join(base,"code","pq_trade"),base]:
    for f in glob.glob(os.path.join(d,"wrds_pull*.py"))+glob.glob(os.path.join(d,"*wrds*.py")):
        show(f,"WRDS SCRIPT",head=2500)
# job bats
for f in ["queue/done/job_wrds_pulls3.bat","queue/done/job_wrds_pulls2.bat.skipped","queue/done/job_wrds_pulls.bat","run_queue_watcher.bat"]:
    show(os.path.join(base,f.replace('/',os.sep)),f)
# search for any pgpass file
p("\n----- PGPASS SEARCH under C:\\Users\\OWNER -----")
found=[]
for root,dirs,files in os.walk(r"C:\Users\OWNER"):
    # prune heavy dirs
    dirs[:]=[d for d in dirs if d.lower() not in ('appdata','anaconda3','node_modules','.git','onedrive') or root.lower().endswith('roaming')]
    for fn in files:
        if 'pgpass' in fn.lower():
            fp=os.path.join(root,fn); found.append(fp)
            p("  FOUND: %s  (%db, mtime %s)"%(fp,os.path.getsize(fp),time.ctime(os.path.getmtime(fp))))
    if len(found)>20: break
if not found: p("  (no pgpass* file found anywhere under C:\\Users\\OWNER)")
# is wrds pkg installed in anaconda?
p("\n----- APPDATA postgresql dir? -----")
pgd=os.path.join(os.environ.get('APPDATA',''),"postgresql")
p("  %s exists: %s"%(pgd, os.path.isdir(pgd)))
open(out,"w").write("\n".join(L)); print("wrote",out)
