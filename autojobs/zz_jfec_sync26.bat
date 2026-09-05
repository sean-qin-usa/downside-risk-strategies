@echo off
setlocal
set PROJ=C:\Users\OWNER\Claude\Projects\GBC Project
cd /d "%PROJ%"
echo START r19b %date% %time%
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJ%\jfec_sync19b.ps1"
echo PS_EXIT=%ERRORLEVEL%
echo END r19b %date% %time%
