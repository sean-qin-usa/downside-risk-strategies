@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
set G=C:\Users\OWNER\Claude\Projects\GBC Project
python -u "%G%\improve_sharpe.py" > "%G%\improve_sharpe.txt" 2>&1
python -u "%G%\autojobs\inverse_vol.py" > "%G%\inverse_vol.txt" 2>&1
python -u "%G%\autojobs\tenor_ladder.py" > "%G%\tenor_ladder.txt" 2>&1
echo BATTERYALLDONE > "%G%\battery_done.txt"
