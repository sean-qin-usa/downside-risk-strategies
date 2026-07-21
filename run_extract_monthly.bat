@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
where python >nul 2>&1 && (python "_extract_monthly.py" > "_monthly_run_log.txt" 2>&1) || (py "_extract_monthly.py" > "_monthly_run_log.txt" 2>&1)
echo FINISHED >> "_monthly_run_log.txt"
