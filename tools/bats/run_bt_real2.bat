@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\bt_real2.py" < nul > "C:\Users\OWNER\Claude\Projects\GBC Project\bt_real2_console.txt" 2>&1
echo BT2DONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\bt_real2_console.txt"
