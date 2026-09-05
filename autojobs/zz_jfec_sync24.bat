@echo off
setlocal
set PROJ=C:\Users\OWNER\Claude\Projects\GBC Project
cd /d "%PROJ%"
echo START sync18 %date% %time%
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJ%\jfec_sync18.ps1"
echo PS_EXIT=%ERRORLEVEL%
echo END sync18 %date% %time%
