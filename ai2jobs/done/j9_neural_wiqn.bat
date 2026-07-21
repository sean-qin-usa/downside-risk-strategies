@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\neural_wiqn.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 neural_wiqn.py > neural_wiqn_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/neural_wiqn_results.json "%G%\neural_wiqn_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/neural_wiqn_log.txt "%G%\neural_wiqn_log.txt"
