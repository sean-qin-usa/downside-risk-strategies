@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\inspect_tpx.py" < nul > "C:\Users\OWNER\Claude\Projects\GBC Project\tpx_inspect_console.txt" 2>&1
echo TPXDONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\tpx_inspect_console.txt"
