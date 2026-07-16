import os, glob, time
base=r"C:\Users\OWNER\Desktop\GBC_data"
out=r"C:\Users\OWNER\Claude\Projects\GBC Project\wrds_diag_out.txt"
L=[]
def p(s): L.append(str(s))
p("DIAG "+time.ctime()); p("base exists: "+str(os.path.isdir(base)))
hb=os.path.join(base,"watcher_heartbeat.txt")
if os.path.exists(hb):
    p("HEARTBEAT: "+open(hb,errors='replace').read().strip())
    p("heartbeat_mtime: "+time.ctime(os.path.getmtime(hb)))
else: p("HEARTBEAT: MISSING")
qd=os.path.join(base,"queue")
p("QUEUE pending: "+str([f for f in os.listdir(qd) if f!='done'] if os.path.isdir(qd) else "NO queue dir"))
done=os.path.join(qd,"done")
if os.path.isdir(done):
    logs=sorted(glob.glob(os.path.join(done,"*")), key=os.path.getmtime, reverse=True)
    p("QUEUE/DONE newest 18:")
    for f in logs[:18]: p("  %s  %s  %db"%(time.ctime(os.path.getmtime(f)),os.path.basename(f),os.path.getsize(f)))
    for f in logs:
        b=os.path.basename(f).lower()
        if 'wrds' in b or 'pull3' in b:
            p("\n----- NEWEST WRDS LOG: "+os.path.basename(f)+" -----")
            p(open(f,errors='replace').read()[-5000:]); break
appdata=os.environ.get('APPDATA','')
for cand in [os.path.join(appdata,"postgresql","pgpass.conf"), os.path.expanduser(r"~\pgpass.conf")]:
    p("PGPASS %s: %s"%(cand,"FOUND" if os.path.exists(cand) else "missing"))
for sub in ["data/wrds","data/raw","results/pq_trade","code/pq_trade"]:
    d=os.path.join(base,sub.replace('/',os.sep))
    if os.path.isdir(d):
        fs=sorted(glob.glob(os.path.join(d,"*")), key=os.path.getmtime, reverse=True)
        p("\n%s (%d files) newest 14:"%(sub,len(fs)))
        for f in fs[:14]: p("  %s  %s  %db"%(time.ctime(os.path.getmtime(f)),os.path.basename(f),os.path.getsize(f)))
    else: p("\n%s : MISSING"%sub)
open(out,"w").write("\n".join(L)); print("wrote",out,len(L),"lines")
