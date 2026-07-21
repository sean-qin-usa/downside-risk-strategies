@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"
"%PYEXE%" "recon_wk.py" > "gowk_out.txt" 2>&1
echo FINWK >> "gowk_out.txt"
