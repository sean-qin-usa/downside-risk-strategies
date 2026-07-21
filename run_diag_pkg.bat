@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\diag_pkg.py" < nul > "C:\Users\OWNER\Claude\Projects\GBC Project\diag_pkg_console.txt" 2>&1
echo PKG_DONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\diag_pkg_console.txt"
