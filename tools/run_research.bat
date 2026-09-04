@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
set G=C:\Users\OWNER\Claude\Projects\GBC Project
python -u "%G%\factor_robust.py" > "%G%\factor_robust.txt" 2>&1
python -u "%G%\strike_robust.py" > "%G%\strike_robust.txt" 2>&1
echo RESEARCHDONE > "%G%\research_done.txt"
