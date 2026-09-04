@echo off
set OUT=C:\Users\OWNER\Claude\Projects\GBC Project\wrds_mon_out.txt
echo === MON %date% %time% === > "%OUT%"
echo --- wrds_done.txt --- >> "%OUT%"
type "C:\GBC_data\wrds_done.txt" >> "%OUT%" 2>&1
echo. >> "%OUT%"
echo --- data\wrds listing --- >> "%OUT%"
dir "C:\GBC_data\data\wrds" >> "%OUT%" 2>&1
echo --- wrds_log.txt --- >> "%OUT%"
type "C:\GBC_data\wrds_log.txt" >> "%OUT%" 2>&1
echo --- queue (pending) --- >> "%OUT%"
dir /b "C:\GBC_data\queue\*.bat" >> "%OUT%" 2>&1
