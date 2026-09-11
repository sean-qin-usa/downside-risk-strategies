@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
echo START %date% %time%
python job_perasset_v2.py > perasset_v2_log.txt 2>&1
echo RC=%errorlevel% %date% %time%
type perasset_v2_log.txt | findstr /C:"DONE" /C:"Traceback" /C:"Error"
