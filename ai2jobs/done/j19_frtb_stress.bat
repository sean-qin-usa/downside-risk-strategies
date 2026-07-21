@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\frtb_stress.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 frtb_stress.py > frtb_stress_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/frtb_stress_results.json "%G%\frtb_stress_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/frtb_stress_log.txt "%G%\frtb_stress_log.txt"
