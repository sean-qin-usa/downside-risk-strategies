@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\bt_covered.py" < nul > "C:\Users\OWNER\Claude\Projects\GBC Project\covered_console.txt" 2>&1
echo COVDONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\covered_console.txt"
