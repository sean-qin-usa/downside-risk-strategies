@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\frtb_neural.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 frtb_neural.py > frtb_neural_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/frtb_neural_results.json "%G%\frtb_neural_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/frtb_neural_log.txt "%G%\frtb_neural_log.txt"
