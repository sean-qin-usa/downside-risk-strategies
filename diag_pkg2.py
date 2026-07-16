import time
out=r"C:\Users\OWNER\Claude\Projects\GBC Project\diag_pkg2_out.txt"
L=[]; p=lambda s:L.append(str(s))
p("DIAG_PKG2 "+time.ctime())
import wrds, os
sqlf=os.path.join(os.path.dirname(wrds.__file__),"sql.py")
src=open(sqlf,errors='replace').read().splitlines()
p("=== lines mentioning username / input / connect / getpass ===")
for i,line in enumerate(src):
    l=line.strip()
    if any(k in line for k in ['username','input(','getpass','def connect','self._username','wrds_username','raw_input','PGUSER','_hostname','def __init__','_username =']):
        p("%4d| %s"%(i,l[:150]))
open(out,"w").write("\n".join(L)); print("wrote",out)
