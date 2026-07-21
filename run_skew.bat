@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
set G=C:\Users\OWNER\Claude\Projects\GBC Project
python -u "%G%\wrds_pull_calls_light.py" > "%G%\calls_light.txt" 2>&1
python -u "%G%\risk_reversal.py" > "%G%\risk_reversal.txt" 2>&1
echo SKEWALLDONE > "%G%\skew_done.txt"
