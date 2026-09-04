@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\bt_anatomy.py" < nul > "C:\Users\OWNER\Claude\Projects\GBC Project\anatomy_console.txt" 2>&1
echo ANATDONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\anatomy_console.txt"
