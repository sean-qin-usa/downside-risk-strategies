@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\heston_sbc.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 heston_sbc.py > heston_sbc_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/heston_sbc_results.json "%G%\heston_sbc_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/heston_sbc_log.txt "%G%\heston_sbc_log.txt"
