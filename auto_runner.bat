@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
set J=C:\Users\OWNER\Claude\Projects\GBC Project\autojobs
if not exist "%J%\done" mkdir "%J%\done"
echo RUNNER STARTED %date% %time% > "%J%\_heartbeat.txt"
:loop
echo %date% %time% > "%J%\_heartbeat.txt"
for %%f in ("%J%\*.bat") do (
  echo === %%~nxf %date% %time% === > "%J%\done\%%~nxf.log"
  call "%%f" < nul >> "%J%\done\%%~nxf.log" 2>&1
  move /y "%%f" "%J%\done\" >nul
)
timeout /t 8 /nobreak >nul
goto loop
