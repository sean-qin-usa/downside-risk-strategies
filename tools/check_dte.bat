@echo off
set OUT=C:\Users\OWNER\Claude\Projects\GBC Project\pull_check_out.txt
echo === CHECK %date% %time% === > "%OUT%"
echo --- pull_dtes_log copy --- >> "%OUT%"
copy /y "C:\Users\OWNER\Claude\Projects\GBC Project\pull_dtes_log.txt" "C:\Users\OWNER\Claude\Projects\GBC Project\pull_dtes_copy.txt" >nul 2>&1
type "C:\Users\OWNER\Claude\Projects\GBC Project\pull_dtes_log.txt" >> "%OUT%" 2>&1
echo. >> "%OUT%"
echo --- new dte output files --- >> "%OUT%"
dir /b "C:\GBC_data\data\wrds\*dte*" >> "%OUT%" 2>&1
echo --- python processes running --- >> "%OUT%"
tasklist /fi "imagename eq python.exe" >> "%OUT%" 2>&1
echo --- CHECK DONE --- >> "%OUT%"
type "%OUT%"
