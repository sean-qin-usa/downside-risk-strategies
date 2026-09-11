@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"
echo === pip install arch === > "go8_out.txt"
"%PYEXE%" -m pip install arch >> "go8_out.txt" 2>&1
echo === run timed7 === >> "go8_out.txt"
"%PYEXE%" "timed7.py" >> "go8_out.txt" 2>&1
echo FIN8 >> "go8_out.txt"
