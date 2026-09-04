import os, time, inspect
out=r"C:\Users\OWNER\Claude\Projects\GBC Project\diag_pkg_out.txt"
L=[]; p=lambda s:L.append(str(s))
p("DIAG_PKG "+time.ctime())
try:
    import wrds
    p("wrds version: "+getattr(wrds,'__version__','?'))
    p("wrds file: "+wrds.__file__)
    try:
        p("Connection.__init__ sig: "+str(inspect.signature(wrds.Connection.__init__)))
    except Exception as e: p("sig err "+str(e))
    # find pgpass handling in source
    src=open(wrds.sql.__file__ if hasattr(wrds,'sql') else wrds.__file__.replace('__init__','sql'),errors='replace').read()
    for i,line in enumerate(src.splitlines()):
        if 'pgpass' in line.lower() or 'expanduser' in line.lower() or 'appdata' in line.lower() or 'PGPASSFILE' in line:
            p("  sql.py:%d  %s"%(i,line.strip()[:140]))
except Exception as e:
    p("import/other err: "+repr(e))
# candidate pgpass locations
home=os.path.expanduser("~")
for c in [os.path.join(home,".pgpass"), os.path.join(os.environ.get('APPDATA',''),"postgresql","pgpass.conf")]:
    p("pgpass candidate %s : %s"%(c, "EXISTS %db"%os.path.getsize(c) if os.path.exists(c) else "missing"))
p("HOME expanduser = "+home)
p("env PGPASSFILE = "+os.environ.get('PGPASSFILE','(unset)'))
open(out,"w").write("\n".join(L)); print("wrote",out)
