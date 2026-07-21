@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\analyze_horizons.py" < nul > "C:\Users\OWNER\Claude\Projects\GBC Project\horizon_console.txt" 2>&1
echo HZDONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\horizon_console.txt"
