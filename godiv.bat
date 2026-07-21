@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"
"%PYEXE%" "divbook.py" > "godiv_out.txt" 2>&1
echo === AI2 CHECK === > "ai2check.txt"
ssh -o BatchMode=yes -o ConnectTimeout=10 ai2 "echo AI2_REACHABLE; hostname; python3 -c \"import torch;print('cuda',torch.cuda.is_available())\"" >> "ai2check.txt" 2>&1
echo FINDIV >> "godiv_out.txt"
