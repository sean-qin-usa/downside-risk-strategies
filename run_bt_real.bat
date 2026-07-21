@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\bt_real.py" < nul > "C:\Users\OWNER\Claude\Projects\GBC Project\bt_real_console.txt" 2>&1
echo BTDONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\bt_real_console.txt"
