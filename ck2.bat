@echo off
set OUT=C:\Users\OWNER\Claude\Projects\GBC Project\pull_check2.txt
echo === CHECK2 %date% %time% === > "%OUT%"
echo --- log tail --- >> "%OUT%"
type "C:\Users\OWNER\Claude\Projects\GBC Project\pull_dtes_log.txt" >> "%OUT%" 2>&1
echo. >> "%OUT%"
echo --- dte output files (count + list) --- >> "%OUT%"
dir /b "C:\GBC_data\data\wrds\*dte*" >> "%OUT%" 2>&1
echo --- python running --- >> "%OUT%"
tasklist /fi "imagename eq python.exe" >> "%OUT%" 2>&1
echo DONE2 >> "%OUT%"
