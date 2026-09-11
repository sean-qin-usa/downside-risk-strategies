@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
echo START %date% %time%
python job_holdout_garch_evt.py > holdout_garch_evt_log.txt 2>&1
echo RC=%errorlevel% %date% %time%
type holdout_garch_evt_log.txt | findstr /C:"HOLDOUTGARCHEVTDONE" /C:"Traceback" /C:"Error"
