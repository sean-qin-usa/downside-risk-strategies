@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\garch_gbm_hybrid.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 garch_gbm_hybrid.py > garch_gbm_hybrid_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/garch_gbm_hybrid_results.json "%G%\garch_gbm_hybrid_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/garch_gbm_hybrid_log.txt "%G%\garch_gbm_hybrid_log.txt"
