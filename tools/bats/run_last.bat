@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
set G=C:\Users\OWNER\Claude\Projects\GBC Project
python -u "%G%\skew_light.py" > "%G%\skew_light.txt" 2>&1
python -u "%G%\earnings.py" > "%G%\earnings.txt" 2>&1
echo LASTDONE > "%G%\last_done.txt"
