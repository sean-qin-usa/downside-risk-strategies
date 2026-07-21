@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\vrp_skew.py" > "C:\Users\OWNER\Claude\Projects\GBC Project\vrp_skew.txt" 2>&1
