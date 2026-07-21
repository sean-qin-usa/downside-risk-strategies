@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\wrds_pull_dtes.py" > "C:\Users\OWNER\Claude\Projects\GBC Project\pull_dtes_log.txt" 2>&1
echo PULL_DTES_DONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\pull_dtes_log.txt"
