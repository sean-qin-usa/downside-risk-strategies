@echo off
set J=C:\Users\OWNER\Claude\Projects\GBC Project\ai2jobs
if not exist "%J%\done" mkdir "%J%\done"
echo AI2 RUNNER STARTED %date% %time%
:loop
echo %date% %time% > "%J%\_hb.txt"
for %%f in ("%J%\*.bat") do (
  call "%%f" > "%J%\done\%%~nxf.log" 2>&1
  move /y "%%f" "%J%\done\" >nul
)
timeout /t 8 /nobreak >nul
goto loop
