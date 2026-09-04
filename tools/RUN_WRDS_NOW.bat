@echo off
set PGFILE=%APPDATA%\postgresql\pgpass.conf
set OUT=C:\Users\OWNER\Claude\Projects\GBC Project\wrds_launch_result.txt
set QD=C:\GBC_data\queue
if not exist "%PGFILE%" ( echo NO_PGPASS_FILE - run setup_pgpass.bat first > "%OUT%" & goto end )
findstr /c:"REPLACE_WITH_YOUR_WRDS_PASSWORD" "%PGFILE%" >nul && ( echo PLACEHOLDER_STILL_PRESENT - open pgpass.conf, replace REPLACE_WITH_YOUR_WRDS_PASSWORD with your real WRDS password, save, then double-click me again > "%OUT%" & goto end )
copy /y "%QD%\done\job_wrds_pulls3.bat" "%QD%\job_wrds_pulls3.bat" >nul
echo QUEUED_OK - watcher will launch the WRDS pull within ~10s. Progress: C:\GBC_data\wrds_log.txt > "%OUT%"
:end
type "%OUT%"
