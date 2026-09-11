@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
echo START %date% %time%
python job_walkforward_hybrid.py > walkforward_hybrid_log.txt 2>&1
echo RC=%errorlevel% %date% %time%
type walkforward_hybrid_log.txt | findstr /C:"WALKFORWARDHYBRIDDONE" /C:"Traceback" /C:"Error"
