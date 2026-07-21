@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\misspec_significance.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 misspec_significance.py > misspec_significance_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/misspec_significance_results.json "%G%\misspec_significance_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/misspec_significance_log.txt "%G%\misspec_significance_log.txt"
