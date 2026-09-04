@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
set G=C:\Users\OWNER\Claude\Projects\GBC Project
python -u "%G%\xasset.py" > "%G%\xasset.txt" 2>&1
python -u "%G%\factor_robust.py" > "%G%\factor_robust2.txt" 2>&1
python -u "%G%\vrp_skew.py" > "%G%\vrp_skew2.txt" 2>&1
echo FINALDONE > "%G%\final_done.txt"
