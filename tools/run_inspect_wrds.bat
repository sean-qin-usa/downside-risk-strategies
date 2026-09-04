@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\inspect_wrds.py" < nul > "C:\Users\OWNER\Claude\Projects\GBC Project\inspect_wrds_console.txt" 2>&1
echo INSPECT_DONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\inspect_wrds_console.txt"
