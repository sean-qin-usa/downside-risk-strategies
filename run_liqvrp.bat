@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\liq_vrp.py" > "C:\Users\OWNER\Claude\Projects\GBC Project\liq_vrp.txt" 2>&1
