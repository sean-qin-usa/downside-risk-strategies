@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
(
echo === where python ===
where python
echo === candidates ===
if exist "%USERPROFILE%\anaconda3\python.exe" echo FOUND %USERPROFILE%\anaconda3\python.exe
if exist "%USERPROFILE%\Anaconda3\python.exe" echo FOUND %USERPROFILE%\Anaconda3\python.exe
if exist "C:\ProgramData\Anaconda3\python.exe" echo FOUND C:\ProgramData\Anaconda3\python.exe
if exist "%USERPROFILE%\miniconda3\python.exe" echo FOUND %USERPROFILE%\miniconda3\python.exe
if exist "C:\ProgramData\anaconda3\python.exe" echo FOUND C:\ProgramData\anaconda3\python.exe
) > "_pyfind.txt" 2>&1

set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"
if exist "C:\ProgramData\anaconda3\python.exe" set "PYEXE=C:\ProgramData\anaconda3\python.exe"
if exist "%USERPROFILE%\miniconda3\python.exe" set "PYEXE=%USERPROFILE%\miniconda3\python.exe"
echo USING %PYEXE% >> "_pyfind.txt"
"%PYEXE%" "_extract3.py" > "_mrun3.txt" 2>&1
echo FIN3 >> "_mrun3.txt"
