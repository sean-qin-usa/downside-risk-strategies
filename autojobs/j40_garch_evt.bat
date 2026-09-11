@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
echo START %date% %time%
python job_garch_evt.py > garch_evt_log.txt 2>&1
echo RC=%errorlevel% %date% %time%
type garch_evt_log.txt | findstr /C:"GARCHEVTDONE" /C:"Traceback" /C:"Error"
