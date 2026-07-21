@echo off
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python -u "C:\Users\OWNER\Claude\Projects\GBC Project\wrds_pull_run2.py" > "C:\Users\OWNER\Claude\Projects\GBC Project\wrds_run2_log.txt" 2>&1
echo RUN2_DONE >> "C:\Users\OWNER\Claude\Projects\GBC Project\wrds_run2_log.txt"
